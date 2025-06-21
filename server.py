from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat
import os
import requests

app = FastAPI()

# ✅ CORS agar bisa diakses dari WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://petroenergisafety.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Payload dari WP Admin
class SertifikatPayload(BaseModel):
    id: int
    nama_peserta: str
    nomor_sertifikat: str
    tanggal: str
    jenis_pelatihan: str
    status: str

@app.post("/generate")
async def generate(payload: SertifikatPayload):
    try:
        if payload.status.lower() != "lulus":
            return {"status": "denied", "message": "❌ Sertifikat hanya untuk peserta dengan status 'lulus'."}

        jenis = payload.jenis_pelatihan.upper()
        if jenis not in ["BFA", "BFF", "WAH"]:
            return {"status": "error", "message": f"❌ Jenis '{jenis}' tidak didukung."}

        # 1️⃣ Generate & Upload Sertifikat
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
            return {"status": "error", "message": "❌ Gagal upload ke Google Drive."}

        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        view_link = upload_result.get("view_link")

        # 2️⃣ Kirim ke WordPress (update kolom file_pdf & file_url)
        post_data = {
            'action': 'update_file_pdf',
            'id': payload.id,
            'file_pdf': download_link,
            'file_url': view_link
        }

        wp_response = requests.post("https://petroenergisafety.com/wp-admin/admin-ajax.php", data=post_data)
        print("🔁 Response WP:", wp_response.text)

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat & diupload.",
            "drive_link": view_link,
            "download_link": download_link,
            "filename": os.path.basename(output_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan."}
    
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
