from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generator import generate_sertifikat
import os
import mysql.connector

app = FastAPI()

# ✅ Izinkan akses dari domain WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Struktur data dari WordPress
class SertifikatPayload(BaseModel):
    id: int
    nama_peserta: str
    nomor_sertifikat: str
    tanggal: str
    jenis_pelatihan: str
    status: str

# ✅ Fungsi update kolom file_pdf ke DB
def update_file_pdf_to_db(id, file_pdf):
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="u148119531_unzpp",
            password="yxlm67baBi",
            database="u148119531_ZLrqe"
        )
        cursor = conn.cursor()

        query = "UPDATE sertifikat_peserta SET file_pdf = %s WHERE id = %s"
        cursor.execute(query, (file_pdf, id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("❌ Database Error:", e)
        return False

# ✅ Endpoint utama: POST dari WP admin
@app.post("/generate")
async def generate(payload: SertifikatPayload):
    try:
        if payload.status.lower() != "lulus":
            return {"status": "denied", "message": "❌ Hanya peserta dengan status 'lulus' yang dibuatkan sertifikat."}

        jenis = payload.jenis_pelatihan.upper()
        if jenis not in ["BFA", "BFF", "WAH"]:
            return {"status": "error", "message": f"❌ Jenis pelatihan '{jenis}' tidak dikenali."}

        # 1️⃣ Generate sertifikat & upload ke Drive
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

        # ✅ Link download langsung dari Drive
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

        # 2️⃣ Simpan hanya kolom file_pdf (tanpa file_url) ke DB
        sukses = update_file_pdf_to_db(payload.id, download_link)
        if not sukses:
            return {"status": "error", "message": "❌ Gagal update kolom file_pdf di database."}

        return {
            "status": "success",
            "message": "✅ Sertifikat berhasil dibuat & disimpan.",
            "download_link": download_link,
            "filename": os.path.basename(output_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ Endpoint tambahan jika ingin mendownload dari server (opsional)
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": "❌ File tidak ditemukan."}
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')