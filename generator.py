import fitz  # PyMuPDF
import os
import base64

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =================== UPLOAD TO GOOGLE DRIVE ===================

def upload_to_drive(local_file_path, filename_drive, folder_id):
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']

        # Cek dan buat file credentials dari Base64 ENV
        base64_creds = os.getenv("GOOGLE_CREDS_BASE64")
        if not base64_creds:
            raise ValueError("❌ Environment variable 'GOOGLE_CREDS_BASE64' tidak ditemukan.")

        with open("service_account_credentials.json", "wb") as f:
            f.write(base64.b64decode(base64_creds))

        SERVICE_ACCOUNT_FILE = 'service_account_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': filename_drive,
            'parents': [folder_id]
        }

        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        return {
            "file_id": file.get('id'),
            "view_link": file.get('webViewLink'),
            "download_link": file.get('webContentLink')
        }

    except Exception as e:
        return {"error": str(e)}

    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'service_account_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': filename_drive,
            'parents': [folder_id]
        }

        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file.get('id')

        # 🛡️ Set permission agar publik bisa akses
        service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        # 🧠 Fetch metadata ulang untuk dapatkan link
        file_info = service.files().get(
            fileId=file_id,
            fields='id, webViewLink, webContentLink'
        ).execute()

        print("🔍 Metadata file:", file_info)  # DEBUG: lihat isi response

        return {
            "file_id": file_info.get('id'),
            "view_link": file_info.get('webViewLink'),
            "download_link": file_info.get('webContentLink')
        }

    except Exception as e:
        print("❌ Upload error:", str(e))  # DEBUG
        return {"error": str(e)}

    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'service_account_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': filename_drive,
            'parents': [folder_id]
        }

        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file.get('id')

        # ➕ Set permission: anyone can view
        service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        # ✅ Ambil metadata ulang untuk dapatkan link
        file = service.files().get(
            fileId=file_id,
            fields='id, webViewLink, webContentLink'
        ).execute()

        return {
            "file_id": file.get('id'),
            "view_link": file.get('webViewLink'),
            "download_link": file.get('webContentLink')
        }

    except Exception as e:
        return {"error": str(e)}

    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'service_account_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': filename_drive,
            'parents': [folder_id]
        }

        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        # Tambahkan ini agar link bisa diakses publik
        service.permissions().create(
            fileId=file.get('id'),
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        return {
            "file_id": file.get('id'),
            "view_link": file.get('webViewLink'),
            "download_link": file.get('webContentLink')
        }

    except Exception as e:
        return {"error": str(e)}

    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'service_account_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': filename_drive,
            'parents': [folder_id]
        }

        media = MediaFileUpload(local_file_path, mimetype='application/pdf')

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Buat file bisa diakses publik
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()

        return {
            "file_id": file.get("id"),
            "view_link": file.get("webViewLink")
        }

    except Exception as e:
        return {"error": str(e)}

# =================== GENERATE PDF SERTIFIKAT ===================

def generate_sertifikat(nama_peserta, nomor_sertifikat, tanggal, jenis_pelatihan):
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
            "nama_h2": (570, 505),
        },
        "BFA": {
            "nomor": (320, 145),
            "nama_h1_y": 345,
            "tanggal": (610, 460),
            "nama_h2": (600, 520),
        },
        "BFF": {
            "nomor": (320, 145),
            "nama_h1_y": 345,
            "tanggal": (610, 455),
            "nama_h2": (570, 505),
        }
    }

    ukurans = {
        "WAH": {"nomor": 20, "nama_h1": 48, "tanggal": 15, "nama_h2": 16},
        "BFA": {"nomor": 20, "nama_h1": 48, "tanggal": 15, "nama_h2": 16},
        "BFF": {"nomor": 20, "nama_h1": 48, "tanggal": 15, "nama_h2": 16},
    }

    if jenis not in templates:
        raise ValueError(f"Template untuk jenis pelatihan '{jenis}' belum tersedia.")

    template_path = templates[jenis]
    koordinat = koordinats[jenis]
    ukuran = ukurans[jenis]

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template tidak ditemukan: {template_path}")

    doc = fitz.open(template_path)
    page1 = doc[0]
    page2 = doc[1]

    def insert_centered_text(page, text, y_pos, fontsize, color):
        page_width = page.rect.width
        text_width = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
        x = (page_width - text_width) / 2
        page.insert_text((x, y_pos), text, fontsize=fontsize, fontname="helv", color=color)

    page1.insert_text(
        koordinat["nomor"],
        nomor_sertifikat,
        fontsize=ukuran["nomor"],
        fontname="helv",
        color=(0, 0, 0)
    )
    insert_centered_text(
        page1,
        nama_peserta,
        koordinat["nama_h1_y"],
        fontsize=ukuran["nama_h1"],
        color=(0.0, 0.2, 0.8)
    )

    page2.insert_text(
        koordinat["tanggal"],
        tanggal,
        fontsize=ukuran["tanggal"],
        fontname="helv",
        color=(0, 0, 0)
    )
    page2.insert_text(
        koordinat["nama_h2"],
        nama_peserta,
        fontsize=ukuran["nama_h2"],
        fontname="helv",
        color=(0, 0, 0)
    )

    if not os.path.exists("output"):
        os.makedirs("output")

    output_filename = f"{nama_peserta.replace(' ', '_')}_{jenis}.pdf"
    output_path = f"output/{output_filename}"
    doc.save(output_path)
    doc.close()

    print(f"✅ Sertifikat berhasil dibuat: {output_path}")

    # Upload ke Google Drive
    upload_result = upload_to_drive(
        local_file_path=output_path,
        filename_drive=output_filename,
        folder_id="1B_Hg5S6GaslwPDrm16RjA4WJ572tL01l"
    )

    print("📤 Upload ke Drive:", upload_result)

    return output_path
