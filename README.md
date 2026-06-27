# 🩺 SiPakar Diet IMT
### Sistem Pakar Penentuan Pola Diet Sehat Berdasarkan Indeks Massa Tubuh

> Kelompok 3 · Program Studi Informatika · Fakultas Teknik
> Universitas Sarjanawiyata Tamansiswa (UST) · Yogyakarta · 2026

---

## 📋 Deskripsi

Sistem Pakar berbasis web yang menggunakan **Mesin Inferensi Rule-Based (IF-THEN)** untuk memberikan rekomendasi pola diet sehat berdasarkan nilai Indeks Massa Tubuh (IMT) dan tingkat aktivitas harian pengguna.

**Tech Stack:**
- **Backend:** Python 3.11+ dengan Flask 3.x
- **Database:** MySQL 8.x dengan PyMySQL
- **Frontend:** HTML5 + Tailwind CSS (CDN) + Chart.js + html2pdf.js
- **Security:** Werkzeug `pbkdf2:sha256` password hashing

---

## 🗂️ Struktur Direktori

```
diet_expert_system/
│
├── app.py                    ← Aplikasi Flask utama (backend + inference engine)
├── schema.sql                ← DDL + 20 aturan basis pengetahuan awal
├── setup.py                  ← Script setup pertama kali
├── requirements.txt          ← Dependensi Python
├── .env.example              ← Template konfigurasi environment
│
└── templates/                ← Template HTML (Jinja2)
    ├── base.html             ← Layout dasar (Tailwind, fonts, Chart.js)
    ├── login.html            ← Halaman login
    ├── register.html         ← Halaman registrasi
    ├── dashboard_user.html   ← Dashboard pengguna (konsultasi + riwayat + grafik)
    ├── hasil_konsultasi.html ← Halaman hasil + PDF (html2pdf.js)
    ├── dashboard_admin.html  ← Dashboard admin (CRUD basis pengetahuan)
    ├── edit_rule.html        ← Form edit aturan (standalone)
    ├── 404.html              ← Error 404
    └── 500.html              ← Error 500
```

---

## ⚙️ Instalasi & Setup

### 1. Prasyarat

- Python 3.11 atau lebih baru
- MySQL 8.0 atau lebih baru
- pip (Python package manager)

### 2. Clone / Buat folder proyek

```bash
mkdir diet_expert_system
cd diet_expert_system
# Salin semua file proyek ke folder ini
```

### 3. Buat virtual environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 4. Install dependensi Python

```bash
pip install -r requirements.txt
```

### 5. Setup Database MySQL

```bash
# Masuk ke MySQL
mysql -u root -p

# Buat database (jika belum ada)
CREATE DATABASE diet_expert_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Jalankan schema SQL (dari terminal, bukan MySQL)
mysql -u root -p diet_expert_system < schema.sql
```

### 6. Konfigurasi environment

```bash
# Salin file konfigurasi
cp .env.example .env

# Edit .env sesuai konfigurasi MySQL Anda
nano .env  # atau gunakan editor favorit
```

Isi `.env`:
```env
SECRET_KEY=ganti-dengan-string-acak-panjang
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password_mysql_anda
DB_NAME=diet_expert_system
FLASK_ENV=development
FLASK_DEBUG=1
```

### 7. Setup admin account

```bash
python setup.py
```

### 8. Jalankan aplikasi

```bash
python app.py
```

Buka browser: **http://localhost:5000**

---

## 🔐 Akun Default

| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `admin123` |
| User  | Daftar sendiri via /register | - |

> **Penting:** Ganti password admin setelah pertama kali login di lingkungan produksi!

---

## 🧠 Cara Kerja Inference Engine

### Algoritma: Forward Chaining (Rule-Based)

```
INPUT:  berat_badan (kg) + tinggi_badan (cm) + aktivitas

STEP 1: Hitung IMT
        IMT = berat_badan / (tinggi_badan / 100)²

STEP 2: Klasifikasi IMT (standar Kemenkes RI)
        IMT < 18.5          → Kurus
        18.5 ≤ IMT ≤ 24.9  → Normal
        25.0 ≤ IMT ≤ 29.9  → Overweight
        30.0 ≤ IMT ≤ 34.9  → Obesitas I
        IMT ≥ 35.0          → Obesitas II

STEP 3: Query Basis Pengetahuan
        SELECT * FROM knowledge_base
        WHERE kategori_imt = [hasil STEP 2]
        AND   aktivitas    = [input aktivitas]

STEP 4: OUTPUT rekomendasi_diet + target_kalori
```

### Contoh Aturan IF-THEN:

```
RULE 2:  IF kategori_imt = 'Normal'     AND aktivitas = 'Sedang'   → Diet Seimbang, 2200 kkal
RULE 9:  IF kategori_imt = 'Overweight' AND aktivitas = 'Sedentari'→ Diet Rendah Kalori, 1500 kkal
RULE 13: IF kategori_imt = 'Obesitas I' AND aktivitas = 'Ringan'   → Diet Terapeutik, 1600 kkal
```

---

## 📊 Fitur Lengkap

### 👤 Pengguna (User)
- ✅ Registrasi akun baru dengan validasi lengkap
- ✅ Login dengan session management aman
- ✅ Form konsultasi IMT dengan validasi JS real-time
- ✅ Pratinjau IMT langsung saat mengetik
- ✅ Mesin inferensi otomatis Rule-Based
- ✅ Halaman hasil konsultasi lengkap dengan skala IMT visual
- ✅ **Unduh hasil sebagai PDF** (html2pdf.js)
- ✅ Riwayat konsultasi dengan tabel lengkap
- ✅ **Grafik perkembangan IMT** (Chart.js line chart)
- ✅ Logout aman dengan penghapusan sesi

### 🔧 Administrator
- ✅ Dashboard statistik (total aturan, pengguna, konsultasi)
- ✅ Tampil semua aturan basis pengetahuan
- ✅ **Tambah** aturan baru dengan preview real-time
- ✅ **Edit** aturan via modal dialog
- ✅ **Hapus** aturan dengan konfirmasi alert
- ✅ Lihat riwayat semua konsultasi pengguna

---

## 🗄️ Struktur Database

### Tabel `user`
| Field | Tipe | Keterangan |
|-------|------|------------|
| id_user | INT PK | Primary key |
| nama | VARCHAR(100) | Nama lengkap |
| username | VARCHAR(50) UNIQUE | Username login |
| password | VARCHAR(255) | Hash pbkdf2:sha256 |
| role | ENUM('admin','user') | Hak akses |
| created_at | DATETIME | Waktu daftar |

### Tabel `knowledge_base`
| Field | Tipe | Keterangan |
|-------|------|------------|
| id_rule | INT PK | Primary key |
| kategori_imt | VARCHAR(30) | Kurus/Normal/Overweight/Obesitas I/II |
| aktivitas | VARCHAR(20) | Sedentari/Ringan/Sedang/Berat |
| rekomendasi_diet | TEXT | Teks rekomendasi lengkap |
| target_kalori | INT | Target kalori harian (kkal) |
| deskripsi_status | TEXT | Analisis status gizi |

### Tabel `consultation`
| Field | Tipe | Keterangan |
|-------|------|------------|
| id_konsultasi | INT PK | Primary key |
| id_user | INT FK | Referensi ke tabel user |
| berat_badan | FLOAT | Berat badan (kg) |
| tinggi_badan | FLOAT | Tinggi badan (cm) |
| usia | INT | Usia (tahun) |
| aktivitas | VARCHAR(20) | Tingkat aktivitas |
| nilai_imt | FLOAT | Nilai IMT hasil perhitungan |
| kategori_imt | VARCHAR(30) | Kategori status gizi |
| rekomendasi_diet | TEXT | Rekomendasi dari inference engine |
| target_kalori | INT | Target kalori harian |
| tanggal_konsultasi | DATETIME | Waktu konsultasi |

---

## 🔒 Keamanan

- Password di-hash menggunakan `werkzeug.security.generate_password_hash` (pbkdf2:sha256)
- Session-based authentication dengan Flask `session`
- Role-based access control (`@login_required`, `@admin_required`)
- Server-side input validation pada semua endpoint POST
- Client-side validation sebagai UX layer (bukan pengganti server-side)
- Parameterized queries untuk mencegah SQL Injection

---

## 📱 Responsif

Antarmuka didesain responsif menggunakan Tailwind CSS:
- ✅ Desktop (1024px+): Sidebar tetap + konten utama
- ✅ Tablet (768px–1023px): Layout adaptif
- ✅ Mobile (<768px): Sidebar toggle + layout stack

---

## 🎓 Referensi

Laporan ini dikembangkan berdasarkan:
- Yosephin, B. (2018). *Tuntunan Praktis Menghitung Kebutuhan Gizi*. ANDI.
- Purwanto & Santoso (2021). Rancang Bangun Sistem Pakar Pola Diet Sehat. JTIIK.
- Kemenkes RI (2014). Pedoman Gizi Seimbang. Permenkes No. 41/2014.

---

## 👥 Tim Pengembang — Kelompok 3

| Nama | NIM |
|------|-----|
| Lucia Tri Wulanningsih | 2024018029 |
| Nurcahyo Syahrul Basuki R. | 2024018055 |
| Hifdzullah Karunia Rizqi | 2024018088 |
| Hifdzullah Anugerah Sejahtera | 2024018094 |

**Dosen Pengampu:** Titik Rahmawati, S.T., M.Cs.
