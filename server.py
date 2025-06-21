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

# ✅ Payload dari WP
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
            return {"status": "denied", "message": "❌ Sertifikat hanya untuk status 'lulus'."}

        jenis = payload.jenis_pelatihan.upper()
        if jenis not in ["BFA", "BFF", "WAH"]:
            return {"status": "error", "message": f"❌ Jenis '{jenis}' tidak didukung."}

        hasil = generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=jenis
        )

        output_path = hasil["output_path"]
        upload_result = hasil["upload_result"]

        print("📦 upload_result:", upload_result)  # 🔍 DEBUG

        file_id = upload_result.get("file_id")
        file_url = upload_result.get("view_link")  # ✅ Link ke Google Drive Viewer

        if not file_id or not file_url:
            return {"status": "error", "message": "❌ Gagal mendapatkan file_id atau file_url dari Drive."}

        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

        # ✅ Kirim ke AJAX WordPress
        post_data = {
            'action': 'update_file_pdf',
            'id': payload.id,
            'file_pdf': download_link,
            'file_url': file_url
        }

        wp_response = requests.post("https://petroenergisafety.com/wp-admin/admin-ajax.php", data=post_data)
        print("🔁 Response update_file_pdf:", wp_response.text)

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat & diupload.",
            "drive_link": file_url,
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
