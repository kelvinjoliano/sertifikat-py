from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from generator import generate_sertifikat
import os

app = FastAPI()

class SertifikatPayload(BaseModel):
    nama_peserta: str
    nomor_sertifikat: str
    tanggal: str
    jenis_pelatihan: str

@app.post("/generate")
async def generate(payload: SertifikatPayload):
    try:
        generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=payload.jenis_pelatihan
        )
        return {"status": "success", "message": "✅ Sertifikat berhasil dibuat"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan"}
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
