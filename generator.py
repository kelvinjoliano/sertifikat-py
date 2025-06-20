import fitz  # PyMuPDF
import os

def generate_sertifikat(nama_peserta, nomor_sertifikat, tanggal, jenis_pelatihan):
    # Mapping template dan koordinat
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
        "WAH": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16,
        },
        "BFA": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16,
        },
        "BFF": {
            "nomor": 20,
            "nama_h1": 48,
            "tanggal": 15,
            "nama_h2": 16,
        }
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

    # Fungsi bantu untuk center teks
    def insert_centered_text(page, text, y_pos, fontsize, color):
        page_width = page.rect.width
        text_width = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
        x = (page_width - text_width) / 2
        page.insert_text((x, y_pos), text, fontsize=fontsize, fontname="helv", color=color)

    # Halaman 1
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

    # Halaman 2
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

    # Simpan hasil ke folder output
    if not os.path.exists("output"):
        os.makedirs("output")
    output_path = f"output/{nama_peserta.replace(' ', '_')}_{jenis}.pdf"
    doc.save(output_path)
    doc.close()

    print(f"✅ Sertifikat berhasil dibuat: {output_path}")


# Contoh pemanggilan (bisa diubah ke jenis lain)
if __name__ == "__main__":
    generate_sertifikat(
        nama_peserta="Kelvin Surya Joliano",
        nomor_sertifikat="PES/WAH/205/V/25",
        tanggal="19-20 Mei 2023",
        jenis_pelatihan="BFF"
    )
