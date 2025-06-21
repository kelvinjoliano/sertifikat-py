from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat, upload_to_drive
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
    id: int  # 🆔 tambahkan ID peserta
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

        # 1️⃣ Generate PDF lokal
        output_path = generate_sertifikat(
            nama_peserta=payload.nama_peserta,
            nomor_sertifikat=payload.nomor_sertifikat,
            tanggal=payload.tanggal,
            jenis_pelatihan=jenis
        )

        # 2️⃣ Upload ke Google Drive
        upload_result = upload_to_drive(
            local_file_path=output_path,
            filename_drive=os.path.basename(output_path),
            folder_id="1B_Hg5S6GaslwPDrm16RjA4WJ572tL01l"
        )

        file_id = upload_result.get("file_id")
        if not file_id:
            return {"status": "error", "message": "❌ Gagal mendapatkan file_id dari Google Drive."}

        # 🔗 Link download langsung dari Google Drive
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

        # 3️⃣ Kirim ke WordPress (update kolom file_pdf)
        post_data = {
            'action': 'update_file_pdf',
            'id': payload.id,
            'file_pdf': download_link
        }

        wp_response = requests.post("https://petroenergisafety.com/wp-admin/admin-ajax.php", data=post_data)
        print("🔁 Response update_file_pdf:", wp_response.text)

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat dan diupload.",
            "drive_link": upload_result.get("view_link"),
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
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
