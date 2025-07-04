import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from generator import generate_sertifikat
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Serve output folder
app.mount("/sertifikat", StaticFiles(directory="output"), name="sertifikat")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://petroenergisafety.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Payload schema ===
class SertifikatPayload(BaseModel):
    nama_peserta: str = Field(..., min_length=1, max_length=100)
    nomor_sertifikat: str = Field(..., min_length=1, max_length=50)
    tanggal: str
    jenis_pelatihan: str
    status: str
    foto_url: str = None  # ➕ Tambahan foto peserta (opsional)

    @validator('tanggal')
    def validate_tanggal(cls, v):
        for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
            try:
                parsed_date = datetime.strptime(v, fmt)
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                continue
        raise ValueError("Format tanggal harus YYYY-MM-DD atau DD-MM-YYYY")

    @validator('nama_peserta')
    def validate_nama_peserta(cls, v):
        if not all(c.isalnum() or c in ' .-' for c in v):
            raise ValueError("Nama peserta hanya boleh berisi huruf, angka, spasi, titik, atau tanda hubung")
        return v

    class Config:
        extra = "ignore"  # Ignore fields like NIK, alamat, dll jika ada


# === POST: /generate ===
@app.post("/generate")
@limiter.limit("5/minute")
async def generate(payload: SertifikatPayload, request: Request):
    logger.info(f"[GENERATE] 🟢 Permintaan dari {request.client.host} | Nama: {payload.nama_peserta}")

    # Validasi status
    if payload.status.lower() != "lulus":
        logger.warning(f"[GENERATE] 🔴 Status bukan lulus: {payload.status}")
        raise HTTPException(status_code=400, detail="Status bukan lulus")

    # Validasi jenis pelatihan
    jenis = payload.jenis_pelatihan.upper()
    if jenis not in ["WAH", "BFA", "BFF"]:
        logger.error(f"[GENERATE] 🔴 Jenis pelatihan tidak valid: {jenis}")
        raise HTTPException(status_code=400, detail=f"Jenis pelatihan '{jenis}' tidak dikenali")

    try:
        # Panggil generator dengan semua data termasuk foto_url
        hasil = generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=jenis,
            foto_url=payload.foto_url
        )

        output_path = hasil["output_path"]
        upload_result = hasil["upload_result"]
        file_id = upload_result.get("file_id")

        if not file_id:
            logger.error(f"[GENERATE] 🔴 Upload gagal: {upload_result.get('error')}")
            raise HTTPException(status_code=500, detail="Gagal upload ke Google Drive")

        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        logger.info(f"[GENERATE] ✅ Sertifikat berhasil: {os.path.basename(output_path)}")

        return {
            "status": "success",
            "message": "Sertifikat berhasil dibuat",
            "download_link": download_link,
            "file_name": os.path.basename(output_path)
        }

    except Exception as e:
        logger.exception(f"[GENERATE] 🔥 Error saat membuat sertifikat")
        raise HTTPException(status_code=500, detail=f"Gagal membuat sertifikat: {str(e)}")


# === GET: /download/{filename} ===
@app.get("/download/{filename}")
@limiter.limit("10/minute")
async def download_file(filename: str, request: Request):
    # Cegah akses path yang berbahaya
    if '..' in filename or '/' in filename or '\\' in filename:
        logger.warning(f"[DOWNLOAD] 🛑 Nama file mencurigakan: {filename}")
        raise HTTPException(status_code=400, detail="Nama file tidak valid")

    file_path = os.path.join("output", filename)
    if not os.path.exists(file_path):
        logger.error(f"[DOWNLOAD] ❌ File tidak ditemukan: {file_path}")
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    logger.info(f"[DOWNLOAD] ⬇️ Mengunduh file: {filename}")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
