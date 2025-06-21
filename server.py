from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat, upload_to_drive
import os

app = FastAPI()

# Aktifkan CORS agar bisa menerima request dari WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://petroenergisafety.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SertifikatPayload(BaseModel):
    nama_peserta: str
    nomor_sertifikat: str
    tanggal: str
    jenis_pelatihan: str
    status: str

@app.post("/generate")
async def generate(payload: SertifikatPayload):
    try:
        if payload.status.lower() != "lulus":
            return {
                "status": "denied",
                "message": "❌ Sertifikat hanya dibuat untuk peserta dengan status 'lulus'."
            }

        jenis_valid = ["BFA", "BFF", "WAH"]
        jenis = payload.jenis_pelatihan.upper()
        if jenis not in jenis_valid:
            return {
                "status": "error",
                "message": f"❌ Jenis pelatihan '{jenis}' tidak didukung untuk pembuatan otomatis."
            }

        # 1. Generate sertifikat PDF secara lokal
        output_path = generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=payload.jenis_pelatihan
        )

        # 2. Upload ke Google Drive
        upload_result = upload_to_drive(
            local_file_path=output_path,
            filename_drive=os.path.basename(output_path),
            folder_id="1B_Hg5S6GaslwPDrm16RjA4WJ572tL01l"
        )

        # 3. Berikan respon ke frontend
        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat dan diupload ke Google Drive.",
            "drive_link": upload_result.get("view_link"),
            "download_link": upload_result.get("download_link"),  # 🔥 ini yang langsung bisa diunduh
            "filename": os.path.basename(output_path)
        }



    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan."}
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
