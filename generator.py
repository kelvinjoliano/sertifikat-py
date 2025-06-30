import fitz  # PyMuPDF
import os
import base64
import time
import requests
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =================== Upload ke Google Drive ===================
def upload_to_drive(local_file_path, filename_drive, folder_id):
    start_time = time.time()
    try:
        print("📤 Mulai upload ke Google Drive...")
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds_file = "service_account_credentials.json"
        use_base64 = False

        if os.path.exists(creds_file):
            print("✅ Menggunakan kredensial dari service_account_credentials.json")
            credentials = service_account.Credentials.from_service_account_file(
                creds_file, scopes=SCOPES)
        else:
            base64_creds = os.getenv("GOOGLE_CREDS_BASE64")
            if not base64_creds:
                raise ValueError("❌ Tidak ditemukan GOOGLE_CREDS_BASE64 atau service_account_credentials.json")

            with open(creds_file, "wb") as f:
                f.write(base64.b64decode(base64_creds))
            print("✅ Kredensial base64 disimpan sementara")
            credentials = service_account.Credentials.from_service_account_file(
                creds_file, scopes=SCOPES)
            use_base64 = True

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {'name': filename_drive, 'parents': [folder_id]}
        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        service.permissions().create(
            fileId=uploaded_file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        print(f"✅ Upload sukses dengan ID: {uploaded_file.get('id')} dalam {time.time() - start_time:.2f} detik")

        if use_base64 and os.path.exists(creds_file):
            os.remove(creds_file)
            print("✅ File kredensial sementara dihapus")

        return {"file_id": uploaded_file.get('id')}

    except Exception as e:
        print(f"❌ Upload gagal: {str(e)}")
        return {"error": str(e)}
    finally:
        if use_base64 and os.path.exists(creds_file):
            try:
                os.remove(creds_file)
                print("✅ File kredensial sementara dihapus setelah error")
            except Exception as cleanup_error:
                print(f"❌ Gagal menghapus file kredensial sementara: {str(cleanup_error)}")


# =================== Generate Sertifikat ===================
def generate_sertifikat(nama_peserta, nomor_sertifikat, tanggal, jenis_pelatihan, foto_url=None):
    start_time = time.time()
    print(f"🧾 Mulai generate sertifikat: {nama_peserta}, {jenis_pelatihan}")

    jenis = jenis_pelatihan.upper()

    templates = {
        "WAH": "templates/WAH.pdf",
        "BFA": "templates/BFA.pdf",
        "BFF": "templates/BFF.pdf"
    }

    koordinats = {
        "WAH": {
            "nomor": (320, 145),
            "nama_h1_y": 345,
            "tanggal": (610, 455),
            "nama_h2": (565, 503)
        },
        "BFA": {
            "nomor": (320, 145),
            "nama_h1_y": 345,
            "tanggal": (610, 460),
            "nama_h2": (580, 503)
        },
        "BFF": {
            "nomor": (320, 145),
            "nama_h1_y": 345,
            "tanggal": (610, 455),
            "nama_h2": (565, 503)
        }
    }

    ukurans = {
        "WAH": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16
        },
        "BFA": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16
        },
        "BFF": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16
        }
    }

    if jenis not in templates:
        raise ValueError(f"Template untuk pelatihan '{jenis}' belum tersedia.")

    template_path = templates[jenis]
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template tidak ditemukan: {template_path}")

    print(f"📄 Template ditemukan: {template_path}")

    doc = fitz.open(template_path)
    page1, page2 = doc[0], doc[1]

    def insert_centered_text(page, text, y_pos, fontsize, color):
        page_width = page.rect.width
        text_width = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
        x = (page_width - text_width) / 2
        page.insert_text((x, y_pos), text, fontsize=fontsize, fontname="helv", color=color)

    koordinat = koordinats[jenis]
    ukuran = ukurans[jenis]

    # Halaman 1
    insert_centered_text(page1, nomor_sertifikat, koordinat["nomor"][1],
                     ukuran["nomor"], (0, 0, 0))
    insert_centered_text(page1, nama_peserta, koordinat["nama_h1_y"],
                         ukuran["nama_h1"], (0, 0, 0))

    # Halaman 2
    page2.insert_text(koordinat["tanggal"], tanggal,
                      fontsize=ukuran["tanggal"], fontname="helv", color=(0, 0, 0))
    page2.insert_text(koordinat["nama_h2"], nama_peserta,
                      fontsize=ukuran["nama_h2"], fontname="helv", color=(0, 0, 0))

    # Tambah Foto ke Halaman 2
        # Tambah Foto ke Halaman 2
    if foto_url:
        try:
            response = requests.get(foto_url)
            if response.status_code == 200:
                img_stream = BytesIO(response.content)

                img_width, img_height = 80, 100
                page_width = page2.rect.width
                x_center = (page_width - img_width) / 2 - 40

                # ⬆ Naikkan posisi dari bawah
                y_bottom = page2.rect.height - 140

                img_rect = fitz.Rect(x_center, y_bottom, x_center + img_width, y_bottom + img_height)
                page2.insert_image(img_rect, stream=img_stream)

                print("🖼️ Foto peserta berhasil ditempel di halaman 2.")
            else:
                print(f"⚠️ Gagal fetch foto: {foto_url}")
        except Exception as e:
            print(f"❌ Error tempel foto: {str(e)}")
    else:
        print("⚠️ Tidak ada foto yang diberikan.")


    os.makedirs("output", exist_ok=True)
    output_filename = f"{nama_peserta.replace(' ', '_')}_{jenis}.pdf"
    output_path = os.path.join("output", output_filename)

    doc.save(output_path)
    doc.close()

    print(f"✅ Sertifikat disimpan di: {output_path} dalam {time.time() - start_time:.2f} detik")

    upload_result = upload_to_drive(
        output_path,
        output_filename,
        folder_id="1B_Hg5S6GaslwPDrm16RjA4WJ572tL01l"
    )

    return {"output_path": output_path, "upload_result": upload_result}
