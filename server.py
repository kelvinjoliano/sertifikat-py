import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from generator import generate_sertifikat
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Izinkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://petroenergisafety.com",
        "http://localhost:3000",  # Untuk testing frontend lokal
        # Tambahkan domain Railway sementara jika perlu
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload dari frontend
class SertifikatPayload(BaseModel):
    nama_peserta: str = Field(..., min_length=1, max_length=100)
    nomor_sertifikat: str = Field(..., min_length=1, max_length=50)
    tanggal: str
    jenis_pelatihan: str
    status: str

    @validator('tanggal')
    def validate_tanggal(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Format tanggal harus YYYY-MM-DD")

    @validator('nama_peserta')
    def validate_nama_peserta(cls, v):
        if not all(c.isalnum() or c in ' .-' for c in v):
            raise ValueError("Nama peserta hanya boleh berisi huruf, angka, spasi, titik, atau tanda hubung")
        return v

# Endpoint untuk generate sertifikat
@app.post("/generate")
@limiter.limit("5/minute")
async def generate(payload: SertifikatPayload, request: Request):
    logger.info(f"Received request to generate certificate for {payload.nama_peserta}")

    if payload.status.lower() != "lulus":
        logger.warning(f"Denied request: Status {payload.status} is not 'lulus'")
        raise HTTPException(status_code=400, detail="Status bukan lulus")

    jenis = payload.jenis_pelatihan.upper()
    if jenis not in ["WAH", "BFA", "BFF"]:
        logger.error(f"Invalid training type: {jenis}")
        raise HTTPException(status_code=400, detail=f"Jenis pelatihan '{jenis}' tidak dikenali")

    try:
        hasil = generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=jenis
        )

        output_path = hasil["output_path"]
        upload_result = hasil["upload_result"]
        file_id = upload_result.get("file_id")

        if not file_id:
            logger.error(f"Failed to upload to Google Drive: {upload_result.get('error')}")
            raise HTTPException(status_code=500, detail="Gagal upload ke Google Drive")

        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        logger.info(f"Certificate generated successfully: {os.path.basename(output_path)}")

        return {
            "status": "success",
            "message": "Sertifikat berhasil dibuat",
            "download_link": download_link,
            "filename": os.path.basename(output_path)
        }

    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal membuat sertifikat: {str(e)}")

# Endpoint untuk download lokal (opsional, perhatikan di Railway)
@app.get("/download/{filename}")
@limiter.limit("10/minute")
async def download_file(filename: str, request: Request):
    # Sanitasi filename untuk mencegah path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        logger.warning(f"Invalid filename attempt: {filename}")
        raise HTTPException(status_code=400, detail="Nama file tidak valid")

    file_path = os.path.join("output", filename)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    logger.info(f"Downloading file: {filename}")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )