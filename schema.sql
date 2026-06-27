-- ============================================================
-- SISTEM PAKAR PENENTUAN POLA DIET SEHAT BERDASARKAN IMT
-- Database Schema - MySQL
-- ============================================================

-- Drop existing database and recreate for clean setup
DROP DATABASE IF EXISTS diet_expert_system;
CREATE DATABASE diet_expert_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE diet_expert_system;

-- ============================================================
-- TABLE: user
-- Stores all registered users (both 'user' and 'admin' roles)
-- ============================================================
CREATE TABLE `user` (
    `id_user`    INT(11)       NOT NULL AUTO_INCREMENT,
    `nama`       VARCHAR(100)  NOT NULL,
    `username`   VARCHAR(50)   NOT NULL UNIQUE,
    `password`   VARCHAR(255)  NOT NULL COMMENT 'Hashed password (werkzeug pbkdf2)',
    `role`       ENUM('admin','user') NOT NULL DEFAULT 'user',
    `created_at` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id_user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: knowledge_base
-- Stores IF-THEN rules used by the Rule-Based Inference Engine
-- Rule: IF kategori_imt = X AND aktivitas = Y THEN rekomendasi_diet, target_kalori
-- ============================================================
CREATE TABLE `knowledge_base` (
    `id_rule`         INT(11)      NOT NULL AUTO_INCREMENT,
    `kategori_imt`    VARCHAR(30)  NOT NULL COMMENT 'Kurus / Normal / Overweight / Obesitas I / Obesitas II',
    `aktivitas`       VARCHAR(20)  NOT NULL COMMENT 'Sedentari / Ringan / Sedang / Berat',
    `rekomendasi_diet` TEXT        NOT NULL COMMENT 'Detailed diet recommendation text',
    `target_kalori`   INT(5)       NOT NULL COMMENT 'Daily calorie target in kcal',
    `deskripsi_status` TEXT        NULL COMMENT 'Brief description of the BMI status',
    PRIMARY KEY (`id_rule`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: consultation
-- Stores each consultation session result per user
-- ============================================================
CREATE TABLE `consultation` (
    `id_konsultasi`    INT(11)      NOT NULL AUTO_INCREMENT,
    `id_user`          INT(11)      NOT NULL,
    `berat_badan`      FLOAT        NOT NULL COMMENT 'Weight in kg',
    `tinggi_badan`     FLOAT        NOT NULL COMMENT 'Height in cm',
    `usia`             INT(3)       NOT NULL COMMENT 'Age in years',
    `aktivitas`        VARCHAR(20)  NOT NULL,
    `nilai_imt`        FLOAT        NOT NULL COMMENT 'Calculated BMI value',
    `kategori_imt`     VARCHAR(30)  NOT NULL,
    `status_gizi`      VARCHAR(30)  NOT NULL,
    `rekomendasi_diet` TEXT         NOT NULL,
    `target_kalori`    INT(5)       NOT NULL,
    `tanggal_konsultasi` DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id_konsultasi`),
    CONSTRAINT `fk_user_consultation` FOREIGN KEY (`id_user`) REFERENCES `user`(`id_user`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- INITIAL DATA: Default Admin Account
-- Password: admin123  (hashed with werkzeug pbkdf2:sha256)
-- ============================================================
INSERT INTO `user` (`nama`, `username`, `password`, `role`) VALUES
('Administrator', 'admin', 'pbkdf2:sha256:600000$8xKz9mNpQwErTyUi$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2', 'admin');

-- NOTE: The admin password hash above is a placeholder.
-- The actual hash for 'admin123' will be generated on first run.
-- Run `python create_admin.py` after setup to create the admin account properly.

-- ============================================================
-- INITIAL DATA: Knowledge Base Rules (20 Rules - Full Matrix)
-- Covering all 5 BMI categories x 4 Activity Levels
-- ============================================================

-- KURUS (Underweight: IMT < 18.5)
INSERT INTO `knowledge_base` (`kategori_imt`, `aktivitas`, `rekomendasi_diet`, `target_kalori`, `deskripsi_status`) VALUES
('Kurus', 'Sedentari',
 'Diet Penambahan Berat Badan Moderat: Tingkatkan asupan kalori dengan makanan bergizi tinggi. Konsumsi karbohidrat kompleks (nasi, roti gandum, ubi) 3x sehari. Protein tinggi dari daging tanpa lemak, telur, dan kacang-kacangan. Tambahkan lemak sehat seperti alpukat, kacang, dan minyak zaitun. Makan 5-6 kali sehari dengan porsi sedang. Hindari junk food meski bertujuan menambah berat badan.',
 2000,
 'Berat badan Anda berada di bawah kisaran ideal. Tubuh kekurangan simpanan energi yang diperlukan untuk fungsi optimal.'),

('Kurus', 'Ringan',
 'Diet Penambahan Berat Badan Ringan Aktif: Konsumsi makanan kalori tinggi dan bergizi seimbang. Sarapan wajib dengan sumber protein dan karbohidrat kompleks. Snack sehat setiap 2-3 jam seperti kacang, yogurt, buah kering. Protein hewani dan nabati di setiap makan utama. Smoothie tinggi kalori dari pisang, susu, dan selai kacang sebagai camilan sore.',
 2200,
 'Berat badan Anda berada di bawah kisaran ideal. Aktivitas ringan yang Anda lakukan memerlukan tambahan asupan energi.'),

('Kurus', 'Sedang',
 'Diet Penambahan Berat Badan Aktif: Kebutuhan energi meningkat akibat aktivitas sedang. Konsumsi karbohidrat kompleks sebagai sumber energi utama. Protein 1.5-2g per kg berat badan ideal per hari dari ikan, daging, kedelai. Minyak kelapa dan alpukat sebagai sumber lemak sehat. Makan sebelum dan sesudah aktivitas fisik. Suplemen protein shake dapat membantu jika sulit mencapai target.',
 2500,
 'Berat badan Anda di bawah ideal dengan aktivitas fisik sedang, tubuh membutuhkan lebih banyak kalori.'),

('Kurus', 'Berat',
 'Diet Penambahan Berat Badan Intensif: Dengan aktivitas berat, kebutuhan kalori sangat tinggi. Perbanyak karbohidrat kompleks: nasi merah, oat, kentang, pasta gandum. Protein sangat tinggi: 2g per kg berat badan ideal. Konsumsi makanan setiap 3 jam tanpa terkecuali. Pre-workout: karbohidrat cepat. Post-workout: protein + karbohidrat dalam 30 menit. Pertimbangkan konsultasi dengan ahli gizi olahraga.',
 2800,
 'Berat badan Anda jauh di bawah ideal sementara aktivitas fisik sangat tinggi, kondisi ini perlu perhatian serius.'),

-- NORMAL (Normal Weight: IMT 18.5 - 24.9)
('Normal', 'Sedentari',
 'Diet Seimbang Pemeliharaan: Pertahankan pola makan sehat untuk menjaga berat badan ideal. Isi separuh piring dengan sayuran dan buah-buahan berwarna beragam. Seperempat piring karbohidrat kompleks, seperempat protein tanpa lemak. Batasi gula tambahan, garam, dan lemak jenuh. Minum air putih minimal 8 gelas per hari. Hindari camilan larut malam dan minuman manis.',
 1800,
 'Selamat! Berat badan Anda berada dalam kisaran ideal. Pertahankan pola hidup sehat ini.'),

('Normal', 'Ringan',
 'Diet Seimbang Aktif Ringan: Pola makan seimbang dengan sedikit peningkatan karbohidrat untuk energi aktivitas. Sarapan bergizi dengan protein dan serat. Makan siang porsi penuh dengan karbohidrat, protein, dan sayuran. Makan malam lebih ringan, kurangi karbohidrat. Snack sehat antara makan utama. Hidrasi yang baik sangat penting.',
 2000,
 'Berat badan Anda ideal dengan aktivitas ringan yang cukup baik untuk kesehatan.'),

('Normal', 'Sedang',
 'Diet Seimbang Aktif Sedang: Tingkatkan asupan karbohidrat kompleks sebagai bahan bakar aktivitas. Protein cukup untuk pemulihan dan pemeliharaan otot. Sayuran dan buah-buahan di setiap waktu makan. Pre-activity meal ringan 1-2 jam sebelum aktivitas. Post-activity: protein dan karbohidrat untuk pemulihan. Pastikan asupan zat besi dan kalsium cukup.',
 2200,
 'Berat badan Anda ideal dengan aktivitas fisik sedang yang sangat baik untuk kesehatan jangka panjang.'),

('Normal', 'Berat',
 'Diet Seimbang Performa Tinggi: Kebutuhan energi tinggi untuk mendukung aktivitas berat. Karbohidrat kompleks sebagai 50-60% total kalori. Protein 1.2-1.7g per kg berat badan. Lemak sehat 25-35% dari total kalori. Waktu makan strategis: pre, intra, dan post-workout nutrition. Suplemen elektrolit penting untuk menggantikan yang hilang saat berolahraga intensif.',
 2600,
 'Berat badan ideal dengan tingkat aktivitas sangat tinggi, Anda butuh nutrisi optimal untuk performa terbaik.'),

-- OVERWEIGHT (Kelebihan Berat Badan: IMT 25.0 - 29.9)
('Overweight', 'Sedentari',
 'Diet Penurunan Berat Badan Bertahap: Kurangi asupan kalori 500 kkal/hari untuk penurunan 0.5kg per minggu. Prioritaskan sayuran, buah rendah kalori, dan protein tanpa lemak. Kurangi drastis gula sederhana, tepung putih, dan lemak jenuh. Makan dalam porsi kecil tapi sering (5-6 kali). Baca label nutrisi dan kontrol porsi dengan mangkuk kecil. Pertimbangkan intermittent fasting 16:8.',
 1500,
 'Berat badan Anda sedikit di atas ideal. Perubahan gaya hidup segera sangat dianjurkan untuk mencegah risiko kesehatan.'),

('Overweight', 'Ringan',
 'Diet Rendah Kalori Aktif Ringan: Defisit kalori moderat dikombinasikan dengan aktivitas. Perbanyak sayuran non-pati (brokoli, bayam, timun) yang mengenyangkan. Protein tinggi membantu pertahankan massa otot saat defisit kalori. Karbohidrat kompleks hanya di pagi dan siang hari. Makan malam: protein + sayuran saja. Hindari alkohol dan minuman berkalori tinggi.',
 1800,
 'Berat badan Anda di atas ideal. Kombinasi diet dan aktivitas ringan akan membantu menurunkan berat badan secara sehat.'),

('Overweight', 'Sedang',
 'Diet Kontrol Kalori Aktif Sedang: Manfaatkan aktivitas sedang untuk mempercepat defisit kalori. Pola makan tinggi protein dan serat untuk kenyang lebih lama. Karbohidrat difokuskan di sekitar waktu aktivitas fisik. Sayuran sebagai bagian terbesar setiap makan. Hindari makanan olahan, fast food, dan minuman manis. Target penurunan 1-2 kg per bulan adalah realistis dan sehat.',
 2000,
 'Berat badan Anda di atas ideal. Aktivitas sedang yang Anda lakukan adalah langkah bagus, dukung dengan pola makan yang lebih baik.'),

('Overweight', 'Berat',
 'Diet Aktif Penurunan Berat Badan: Meski aktif, perhatikan kualitas makanan lebih dari kuantitas. Jangan gunakan aktivitas sebagai alasan makan berlebih. Protein tinggi untuk mendukung massa otot dan rasa kenyang. Karbohidrat strategis hanya sebelum dan sesudah latihan berat. Lemak sehat dalam jumlah terkontrol. Prioritaskan makanan utuh dan hindari suplemen dengan kalori tersembunyi.',
 2200,
 'Berat badan Anda sedikit di atas ideal meski aktif secara fisik. Perbaikan pola makan akan memberikan hasil signifikan.'),

-- OBESITAS I (Obese Class I: IMT 30.0 - 34.9)
('Obesitas I', 'Sedentari',
 'Diet Terapeutik Obesitas: Konsultasi dengan dokter dan ahli gizi sangat dianjurkan. Defisit kalori terkontrol 500-750 kkal/hari. Eliminasi total gula tambahan, minuman manis, fast food, dan makanan olahan. Protein tinggi di setiap makan untuk mempertahankan massa otot. Sayuran hijau sebagai makanan utama. Perkenalkan aktivitas fisik ringan secara bertahap (jalan kaki 15-30 menit/hari). Pantau perkembangan setiap minggu.',
 1400,
 'Anda mengalami obesitas tingkat pertama. Kondisi ini meningkatkan risiko diabetes tipe 2, hipertensi, dan penyakit jantung.'),

('Obesitas I', 'Ringan',
 'Diet Penurunan Berat Badan Aktif: Kombinasi defisit kalori dan aktivitas ringan yang sudah Anda lakukan adalah permulaan yang baik. Fokus pada makanan dengan densitas gizi tinggi namun kalori rendah. Tingkatkan konsumsi serat larut (oat, apel, kacang) untuk kontrol gula darah. Protein tanpa lemak di setiap makan utama. Rencanakan menu mingguan untuk menghindari pilihan impulsif yang tidak sehat.',
 1600,
 'Anda mengalami obesitas tingkat pertama. Aktivitas ringan yang Anda lakukan adalah langkah awal yang baik.'),

('Obesitas I', 'Sedang',
 'Diet Aktif Penurunan Serius: Aktivitas sedang Anda adalah modal besar. Kurangi karbohidrat sederhana secara signifikan. Pola makan Mediterranean atau DASH diet sangat dianjurkan. Protein hewani lean dan protein nabati dalam jumlah cukup. Lemak sehat dari ikan, kacang, dan minyak zaitun. Monitor kadar gula darah dan tekanan darah secara rutin. Target realistis: turun 5-10% dari berat badan awal dalam 3-6 bulan.',
 1800,
 'Anda mengalami obesitas tingkat pertama. Namun aktivitas sedang yang Anda miliki memberikan keuntungan metabolik yang baik.'),

('Obesitas I', 'Berat',
 'Diet Rehabilitasi Aktif Intensif: Perhatian: aktivitas berat dengan obesitas memerlukan pengawasan medis. Pastikan sendi dan kardiovaskular dalam kondisi baik sebelum aktivitas intensif. Nutrisi sport yang tepat sangat penting. Kalori dikurangi tapi tidak terlalu drastis karena kebutuhan aktivitas. Protein sangat tinggi untuk recovery dan preservasi otot. Karbohidrat timed di sekitar latihan. Istirahat dan pemulihan yang cukup wajib.',
 2000,
 'Anda mengalami obesitas tingkat pertama dengan aktivitas fisik tinggi. Pengawasan medis sangat dianjurkan.'),

-- OBESITAS II (Obese Class II: IMT ≥ 35.0)
('Obesitas II', 'Sedentari',
 'Diet Medis Obesitas Berat: WAJIB berkonsultasi dengan dokter sebelum memulai program diet apapun. Kemungkinan diperlukan intervensi medis (obat penurun berat badan, operasi bariatrik). Program diet harus dalam pengawasan tenaga medis profesional. Perubahan pola makan sangat drastis: eliminasi semua makanan berkalori kosong. Mulai dengan aktivitas fisik sangat ringan seperti jalan kaki 10 menit. Dukungan psikologis mungkin diperlukan untuk perubahan perilaku jangka panjang.',
 1200,
 'Anda mengalami obesitas tingkat dua yang serius. Kondisi ini memerlukan intervensi medis dan program diet terpantau.'),

('Obesitas II', 'Ringan',
 'Diet Medis Terpantau Aktif Ringan: Konsultasi medis wajib. Meski aktivitas ringan sudah dimulai, tetap diperlukan pengawasan dokter. Diet sangat rendah kalori harus direncanakan dengan ahli gizi. Fokus pada makanan utuh, sayuran, dan protein lean. Hindari semua makanan ultraproses. Tingkatkan aktivitas secara sangat bertahap untuk menghindari cedera. Pemeriksaan kesehatan rutin sangat penting.',
 1400,
 'Anda mengalami obesitas tingkat dua. Aktivitas ringan yang Anda mulai adalah langkah positif, namun supervisi medis tetap diperlukan.'),

('Obesitas II', 'Sedang',
 'Diet Rehabilitasi Komprehensif: Meski memiliki aktivitas sedang, kondisi obesitas II tetap serius. Program diet komprehensif dengan tim medis (dokter, ahli gizi, fisioterapis). Pola makan sangat bersih: sayuran, protein lean, lemak sehat dalam porsi terkontrol ketat. Hindari semua pemicu makan berlebih. Journaling makanan dan emosi sangat membantu. Target jangka panjang realistis: turun 10-20% berat badan dalam 6-12 bulan.',
 1600,
 'Anda mengalami obesitas tingkat dua. Aktivitas sedang yang Anda lakukan adalah keuntungan, tetapi program komprehensif tetap diperlukan.'),

('Obesitas II', 'Berat',
 'Diet Medis Khusus Aktif Intensif: Kondisi langka dan memerlukan evaluasi medis menyeluruh. Kemampuan beraktivitas berat dengan obesitas II mungkin mengindikasikan massa otot tinggi, konfirmasi dengan pengukuran body composition. Jika memang kondisi gemuk-atletik, program nutrisi harus sangat personal. Bersama dokter olahraga dan ahli gizi olahraga, rancang program defisit kalori yang tidak mengorbankan performa. Monitoring kesehatan sangat intensif.',
 1800,
 'Obesitas tingkat dua dengan aktivitas berat adalah kondisi yang memerlukan evaluasi dan penanganan medis khusus yang komprehensif.');

-- ============================================================
-- Create index for faster queries
-- ============================================================
CREATE INDEX idx_knowledge_rule ON `knowledge_base` (`kategori_imt`, `aktivitas`);
CREATE INDEX idx_consultation_user ON `consultation` (`id_user`);
CREATE INDEX idx_consultation_date ON `consultation` (`tanggal_konsultasi`);

-- ============================================================
-- Verification Query
-- ============================================================
SELECT 'Schema created successfully!' AS status;
SELECT COUNT(*) AS total_rules FROM knowledge_base;
