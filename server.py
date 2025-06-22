from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat
import os
import mysql.connector

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

# ✅ Fungsi simpan langsung ke database (file_url saja)
def update_file_links_to_db(id, file_url):
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="u148119531_unzpp",
            password="yxlm67baBi",
            database="u148119531_ZLrqe"
        )
        cursor = conn.cursor()

        query = "UPDATE sertifikat_peserta SET file_url = %s WHERE id = %s"
        cursor.execute(query, (file_url, id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("❌ DB Error:", e)
        return False

# ✅ Endpoint utama
@app.post("/generate")
async def generate(payload: SertifikatPayload):
    try:
        if payload.status.lower() != "lulus":
            return {"status": "denied", "message": "❌ Sertifikat hanya untuk peserta dengan status 'lulus'."}

        jenis = payload.jenis_pelatihan.upper()
        if jenis not in ["BFA", "BFF", "WAH"]:
            return {"status": "error", "message": f"❌ Jenis '{jenis}' tidak didukung."}

        # 1️⃣ Generate PDF & Upload ke Drive
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

        view_link = upload_result.get("view_link")

        # 2️⃣ Simpan hanya view_link ke kolom file_url
        sukses = update_file_links_to_db(payload.id, view_link)
        if not sukses:
            return {"status": "error", "message": "❌ Gagal menyimpan ke database (file_url)."}

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat & disimpan ke database.",
            "drive_link": view_link,
            "filename": os.path.basename(output_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ Endpoint download file lokal jika dibutuhkan
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan."}
    
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
