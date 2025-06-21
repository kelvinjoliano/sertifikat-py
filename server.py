from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat
import os
import requests

app = FastAPI()

# ✅ Izinkan akses dari domain WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://petroenergisafety.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Model data yang dikirim dari WordPress
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
        # ❌ Tolak jika belum lulus
        if payload.status.lower() != "lulus":
            return {"status": "denied", "message": "❌ Sertifikat hanya untuk status 'lulus'."}

        # ❌ Validasi jenis pelatihan
        jenis = payload.jenis_pelatihan.upper()
        if jenis not in ["BFA", "BFF", "WAH"]:
            return {"status": "error", "message": f"❌ Jenis '{jenis}' tidak didukung."}

        # ✅ Generate dan upload ke Drive
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
            return {"status": "error", "message": "❌ Gagal upload ke Drive."}

        # ✅ Link download dan view dari Google Drive
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        view_link = upload_result.get("view_link")

        # ✅ Kirim ke WordPress via AJAX
        post_data = {
            'action': 'update_file_pdf',
            'id': payload.id,
            'file_pdf': download_link,
            'file_url': view_link  # <- untuk kolom WPDA
        }

        print("📦 Data ke WordPress:", post_data)

        wp_response = requests.post("https://petroenergisafety.com/wp-admin/admin-ajax.php", data=post_data)
        print("🔁 Response update_file_pdf:", wp_response.text)

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat & diupload.",
            "drive_link": view_link,
            "download_link": download_link,
            "filename": os.path.basename(output_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ Endpoint untuk download file lokal (optional)
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan."}
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
