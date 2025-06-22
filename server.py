from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat
import os

app = FastAPI()

# Izinkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://petroenergisafety.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload dari frontend
class SertifikatPayload(BaseModel):
    nama_peserta: str
    nomor_sertifikat: str
    tanggal: str
    jenis_pelatihan: str
    status: str

# Endpoint untuk generate
@app.post("/generate")
async def generate(payload: SertifikatPayload):
    if payload.status.lower() != "lulus":
        return {"status": "denied", "message": "Status bukan lulus"}

    jenis = payload.jenis_pelatihan.upper()
    if jenis not in ["WAH", "BFA", "BFF"]:
        return {"status": "error", "message": f"Jenis pelatihan '{jenis}' tidak dikenali"}

    hasil = generate_sertifikat(
        nama_peserta=payload.nama_peserta,
        nomor_sertifikat=payload.nomor_sertifikat,
        tanggal=payload.tanggal,
        jenis_pelatihan=jenis
    )

    output_path = hasil["output_path"]
    file_id = hasil["upload_result"].get("file_id")

    if not file_id:
        return {"status": "error", "message": "Gagal upload ke Google Drive"}

    download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

    return {
        "status": "success",
        "message": "Sertifikat berhasil dibuat",
        "download_link": download_link,
        "filename": os.path.basename(output_path)
    }

# (Opsional) endpoint download lokal
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File tidak ditemukan"}
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
