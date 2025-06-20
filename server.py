from fastapi import FastAPI, Request
from pydantic import BaseModel
from generator import generate_sertifikat

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
