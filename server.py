import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import fitz  # PyMuPDF

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

TEMPLATE_PATHS = {
    "WAH": "templates/WAH_template.pdf",
    "BFA": "templates/BFA_template.pdf",
    "BFF": "templates/BFF_template.pdf"
}

OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_sertifikat(nama_peserta, nomor_sertifikat, tanggal, jenis_pelatihan):
    jenis = jenis_pelatihan.upper()
    template_file = TEMPLATE_PATHS.get(jenis)
    if not template_file or not os.path.exists(template_file):
        raise Exception(f"Template untuk pelatihan '{jenis}' tidak ditemukan.")

    doc = fitz.open(template_file)

    # Halaman 1
    page1 = doc[0]
    page1.insert_text((210, 290), nama_peserta, fontsize=16, fontname="helv", fill=(0, 0, 0))
    page1.insert_text((210, 330), nomor_sertifikat, fontsize=12, fontname="helv", fill=(0, 0, 0))
    page1.insert_text((210, 370), jenis_pelatihan.upper(), fontsize=12, fontname="helv", fill=(0, 0, 0))
    page1.insert_text((450, 450), tanggal, fontsize=12, fontname="helv", fill=(0, 0, 0))

    # Halaman 2
    if len(doc) > 1:
        page2 = doc[1]
        page2.insert_text((150, 500), jenis_pelatihan.upper(), fontsize=14, fontname="helv", fill=(0, 0, 0))

    filename = f"{nama_peserta.replace(' ', '_')}_{jenis}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)
    doc.save(output_path)
    doc.close()
    return output_path

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def file_exists(service, folder_id, filename):
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, webViewLink)").execute()
    files = results.get('files', [])
    if files:
        return files[0]  # file sudah ada
    return None

def upload_to_drive(local_file_path, filename_drive, folder_id):
    service = get_drive_service()

    # ✅ Cek apakah file sudah ada
    existing_file = file_exists(service, folder_id, filename_drive)
    if existing_file:
        print("✅ File sudah ada di Drive, tidak diupload ulang.")
        return {
            "file_id": existing_file['id'],
            "view_link": existing_file.get("webViewLink")
        }

    # 🔁 Upload baru jika belum ada
    file_metadata = {
        'name': filename_drive,
        'parents': [folder_id]
    }
    media = MediaFileUpload(local_file_path, mimetype='application/pdf')
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

    return {
        "file_id": uploaded.get("id"),
        "view_link": uploaded.get("webViewLink")
    }
