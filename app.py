# ============================================================
# SISTEM PAKAR PENENTUAN POLA DIET SEHAT BERDASARKAN IMT
# Backend: Flask (Python)
# Implements: Rule-Based Inference Engine, Auth, CRUD
# ============================================================

import os
import json
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    g,
)
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import pymysql.cursors

# ============================================================
# APPLICATION SETUP
# ============================================================
app = Flask(__name__)

# Secret key for session management — change to a long random string in production
app.secret_key = os.environ.get("SECRET_KEY", "diet-expert-secret-key-2026-ustyk")

# ============================================================
# DATABASE CONFIGURATION
# Update these values to match your MySQL setup
# ============================================================

from urllib.parse import urlparse

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # ── JIKA ONLINE (DI SERVER RAILWAY & AIVEN) ──
    clean_url = DATABASE_URL.replace("mysql+pymysql://", "mysql://")
    url = urlparse(clean_url)

    DB_CONFIG = {
        "host": url.hostname,
        "user": url.username,
        "password": url.password,
        "port": url.port or 3306,
        "db": url.path.lstrip("/"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
        "ssl": {},  # <── GANTI BAGIAN INI (Cukup kasih dict kosong buat aktifin SSL di PyMySQL)
    }
else:
    # ── JIKA LOKAL (DI LAPTOP KAMU) ──
    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "db": os.environ.get("DB_NAME", "diet_expert_system"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }


# ============================================================
# DATABASE HELPERS
# ============================================================
def get_db():
    """Get a database connection, reusing per-request connection."""
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False, commit=False):
    """
    Execute a SQL query and return results.
    Args:
        sql     : SQL string (use %s for placeholders)
        args    : tuple of parameters
        one     : return only first row if True
        commit  : used for INSERT/UPDATE/DELETE
    Returns:
        For SELECT: list of dicts or single dict
        For INSERT: lastrowid
        For UPDATE/DELETE: rowcount
    """
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(sql, args)
        if commit:
            conn.commit()
            # Return lastrowid for INSERT, rowcount for others
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        result = cursor.fetchone() if one else cursor.fetchall()
    return result


# ============================================================
# AUTHENTICATION DECORATORS
# ============================================================
def login_required(f):
    """Decorator: Requires user to be logged in."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator: Requires user to have admin role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Akses ditolak. Halaman ini hanya untuk Admin.", "danger")
            return redirect(url_for("dashboard_user"))
        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# RULE-BASED INFERENCE ENGINE
# The core expert system logic
# ============================================================
def classify_bmi(imt_value: float) -> str:
    """
    Classify BMI value into nutritional status category
    following Indonesian Ministry of Health (Kemenkes RI) standards.

    Batas kategori menggunakan operator < dan >= agar tidak ada celah
    di antara kategori akibat floating point (misal 24.97 masuk Normal, bukan Obesitas).

    Standar Kemenkes RI / WHO:
        Kurus      : IMT < 18.5
        Normal     : 18.5 <= IMT < 25.0
        Overweight : 25.0 <= IMT < 30.0
        Obesitas I : 30.0 <= IMT < 35.0
        Obesitas II: IMT >= 35.0

    Args:
        imt_value (float): Calculated BMI value (nilai mentah, sebelum di-round)

    Returns:
        str: Category name (Kurus / Normal / Overweight / Obesitas I / Obesitas II)
    """
    if imt_value < 18.5:
        return "Kurus"
    elif imt_value < 25.0:
        return "Normal"
    elif imt_value < 30.0:
        return "Overweight"
    elif imt_value < 35.0:
        return "Obesitas I"
    else:
        return "Obesitas II"


def run_inference_engine(kategori_imt: str, aktivitas: str) -> dict | None:
    """
    Rule-Based Inference Engine.
    Matches the user's BMI category and activity level against
    the knowledge base (IF-THEN rules) to produce a diet recommendation.

    Algorithm: Forward Chaining
    - Given FACTS: kategori_imt AND aktivitas
    - Match against RULES in knowledge_base table
    - Return CONCLUSION: rekomendasi_diet + target_kalori

    Args:
        kategori_imt (str): BMI category from classify_bmi()
        aktivitas    (str): User's activity level

    Returns:
        dict: Matched rule with recommendation or None if no match
    """
    rule = query_db(
        """
        SELECT id_rule, kategori_imt, aktivitas,
               rekomendasi_diet, target_kalori, deskripsi_status
        FROM knowledge_base
        WHERE kategori_imt = %s AND aktivitas = %s
        LIMIT 1
        """,
        (kategori_imt, aktivitas),
        one=True,
    )
    return rule


def calculate_bmi(berat_kg: float, tinggi_cm: float) -> float:
    """
    Calculate Body Mass Index (BMI / IMT).
    Formula: BMI = Weight(kg) / Height(m)^2

    Args:
        berat_kg   (float): Weight in kilograms
        tinggi_cm  (float): Height in centimeters

    Returns:
        float: BMI value rounded to 2 decimal places
    """
    tinggi_m = tinggi_cm / 100.0
    imt = berat_kg / (tinggi_m**2)
    return round(imt, 2)


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================
@app.route("/")
def index():
    """Root route: redirect based on auth state."""
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("dashboard_admin"))
        return redirect(url_for("dashboard_user"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page.
    GET  : Show login form
    POST : Validate credentials, create session, redirect by role
    """
    # Already logged in — redirect
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # --- Server-side validation ---
        errors = []
        if not username:
            errors.append("Username tidak boleh kosong.")
        if not password:
            errors.append("Password tidak boleh kosong.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("login.html", username=username)

        # --- Query user from database ---
        user = query_db(
            "SELECT * FROM `user` WHERE username = %s LIMIT 1", (username,), one=True
        )

        # --- Verify password hash ---
        if user and check_password_hash(user["password"], password):
            # Valid credentials — create session
            session.clear()
            session["user_id"] = user["id_user"]
            session["username"] = user["username"]
            session["nama"] = user["nama"]
            session["role"] = user["role"]

            flash(f"Selamat datang, {user['nama']}!", "success")

            # Role-based redirect
            if user["role"] == "admin":
                return redirect(url_for("dashboard_admin"))
            return redirect(url_for("dashboard_user"))
        else:
            flash("Username atau password salah. Silakan coba lagi.", "danger")
            return render_template("login.html", username=username)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration page.
    GET  : Show registration form
    POST : Validate input, hash password, insert user, redirect to login
    """
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- Server-side validation ---
        errors = []
        if not nama:
            errors.append("Nama lengkap tidak boleh kosong.")
        if len(nama) < 2:
            errors.append("Nama terlalu pendek (minimal 2 karakter).")
        if not username:
            errors.append("Username tidak boleh kosong.")
        if len(username) < 4:
            errors.append("Username terlalu pendek (minimal 4 karakter).")
        if not username.isalnum():
            errors.append("Username hanya boleh berisi huruf dan angka.")
        if not password:
            errors.append("Password tidak boleh kosong.")
        if len(password) < 6:
            errors.append("Password terlalu pendek (minimal 6 karakter).")
        if password != confirm:
            errors.append("Konfirmasi password tidak cocok.")

        # Check username uniqueness
        if not errors:
            existing = query_db(
                "SELECT id_user FROM `user` WHERE username = %s", (username,), one=True
            )
            if existing:
                errors.append(
                    f'Username "{username}" sudah digunakan. Pilih username lain.'
                )

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", nama=nama, username=username)

        # --- Hash password and insert user ---
        hashed_pw = generate_password_hash(password)
        query_db(
            "INSERT INTO `user` (nama, username, password, role) VALUES (%s, %s, %s, %s)",
            (nama, username, hashed_pw, "user"),
            commit=True,
        )

        flash("Registrasi berhasil! Silakan login dengan akun Anda.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    """Clear session and redirect to login."""
    nama = session.get("nama", "Pengguna")
    session.clear()
    flash(f"Sampai jumpa, {nama}! Anda telah logout.", "info")
    return redirect(url_for("login"))


# ============================================================
# USER ROUTES
# ============================================================
@app.route("/dashboard")
@login_required
def dashboard_user():
    """
    User dashboard.
    Displays: Welcome message, consultation form, history table, BMI chart data
    """
    if session.get("role") == "admin":
        return redirect(url_for("dashboard_admin"))

    user_id = session["user_id"]

    # Fetch consultation history (newest first)
    history = query_db(
        """
        SELECT id_konsultasi, berat_badan, tinggi_badan, usia,
               aktivitas, nilai_imt, kategori_imt, status_gizi,
               rekomendasi_diet, target_kalori,
               DATE_FORMAT(tanggal_konsultasi, '%%d %%M %%Y %%H:%%i') AS tgl_fmt,
               tanggal_konsultasi
        FROM consultation
        WHERE id_user = %s
        ORDER BY tanggal_konsultasi DESC
        LIMIT 20
        """,
        (user_id,),
    )

    # Prepare Chart.js data: BMI over time (chronological, max 10 points)
    chart_data = query_db(
        """
        SELECT nilai_imt, DATE_FORMAT(tanggal_konsultasi, '%%d/%%m') AS tgl_label
        FROM consultation
        WHERE id_user = %s
        ORDER BY tanggal_konsultasi ASC
        LIMIT 10
        """,
        (user_id,),
    )
    chart_labels = [r["tgl_label"] for r in chart_data] if chart_data else []
    chart_values = [r["nilai_imt"] for r in chart_data] if chart_data else []

    # Activity level options for the consultation form
    activity_options = ["Sedentari", "Ringan", "Sedang", "Berat"]

    return render_template(
        "dashboard_user.html",
        history=history,
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values),
        activity_options=activity_options,
    )


@app.route("/konsultasi", methods=["POST"])
@login_required
def konsultasi():
    """
    Process BMI consultation form.
    1. Validate inputs
    2. Calculate BMI
    3. Classify BMI category
    4. Run Rule-Based Inference Engine
    5. Save result to consultation table
    6. Redirect to result page
    """
    if session.get("role") == "admin":
        flash("Admin tidak dapat melakukan konsultasi IMT.", "warning")
        return redirect(url_for("dashboard_admin"))

    # --- Get form data ---
    nama_p = request.form.get("nama_pasien", session["nama"]).strip()
    berat_s = request.form.get("berat_badan", "").strip()
    tinggi_s = request.form.get("tinggi_badan", "").strip()
    usia_s = request.form.get("usia", "").strip()
    aktivitas = request.form.get("aktivitas", "").strip()

    # --- Server-side validation ---
    errors = []
    activity_valid = ["Sedentari", "Ringan", "Sedang", "Berat"]

    if not berat_s:
        errors.append("Berat badan harus diisi.")
    if not tinggi_s:
        errors.append("Tinggi badan harus diisi.")
    if not usia_s:
        errors.append("Usia harus diisi.")
    if aktivitas not in activity_valid:
        errors.append("Pilihan tingkat aktivitas tidak valid.")

    # Numeric validation
    berat = None
    tinggi = None
    usia = None

    if berat_s:
        try:
            berat = float(berat_s)
            if berat <= 0:
                errors.append("Berat badan harus lebih dari 0 kg.")
            if berat > 500:
                errors.append("Berat badan tidak valid (maksimal 500 kg).")
        except ValueError:
            errors.append("Berat badan harus berupa angka.")

    if tinggi_s:
        try:
            tinggi = float(tinggi_s)
            if tinggi <= 0:
                errors.append("Tinggi badan harus lebih dari 0 cm.")
            if tinggi < 50 or tinggi > 300:
                errors.append("Tinggi badan tidak valid (50–300 cm).")
        except ValueError:
            errors.append("Tinggi badan harus berupa angka.")

    if usia_s:
        try:
            usia = int(usia_s)
            if usia < 18:
                errors.append("Sistem hanya untuk pengguna berusia 18 tahun ke atas.")
            if usia > 60:
                errors.append("Sistem hanya untuk pengguna berusia maksimal 60 tahun.")
        except ValueError:
            errors.append("Usia harus berupa angka bulat.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("dashboard_user"))

    # ======================================================
    # INFERENCE ENGINE — Core Expert System Logic
    # ======================================================

    # Step 1: Calculate BMI
    nilai_imt = calculate_bmi(berat, tinggi)

    # Step 2: Classify BMI into nutritional category
    kategori_imt = classify_bmi(nilai_imt)

    # Step 3: Run Rule-Based Inference — match against knowledge base
    rule_result = run_inference_engine(kategori_imt, aktivitas)

    if not rule_result:
        # Fallback: no matching rule found in knowledge base
        flash(
            f'Aturan untuk kombinasi IMT "{kategori_imt}" dan aktivitas "{aktivitas}" '
            "belum tersedia di basis pengetahuan. Hubungi Admin.",
            "warning",
        )
        return redirect(url_for("dashboard_user"))

    rekomendasi_diet = rule_result["rekomendasi_diet"]
    target_kalori = rule_result["target_kalori"]
    deskripsi_status = rule_result.get("deskripsi_status", "")

    # Step 4: Save consultation result to database
    user_id = session["user_id"]
    konsultasi_id = query_db(
        """
        INSERT INTO consultation
            (id_user, berat_badan, tinggi_badan, usia, aktivitas,
             nilai_imt, kategori_imt, status_gizi,
             rekomendasi_diet, target_kalori)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            berat,
            tinggi,
            usia,
            aktivitas,
            nilai_imt,
            kategori_imt,
            kategori_imt,
            rekomendasi_diet,
            target_kalori,
        ),
        commit=True,
    )

    # Step 5: Store result in session for display on result page
    session["last_result"] = {
        "id": konsultasi_id,
        "nama_pasien": nama_p,
        "berat_badan": berat,
        "tinggi_badan": tinggi,
        "usia": usia,
        "aktivitas": aktivitas,
        "nilai_imt": nilai_imt,
        "kategori_imt": kategori_imt,
        "status_gizi": kategori_imt,
        "deskripsi_status": deskripsi_status,
        "rekomendasi_diet": rekomendasi_diet,
        "target_kalori": target_kalori,
        "tanggal": datetime.now().strftime("%d %B %Y, %H:%M"),
    }

    return redirect(url_for("hasil_konsultasi"))


@app.route("/hasil")
@login_required
def hasil_konsultasi():
    """Display the result of the most recent consultation."""
    if session.get("role") == "admin":
        return redirect(url_for("dashboard_admin"))

    result = session.pop("last_result", None)
    if not result:
        flash("Tidak ada hasil konsultasi untuk ditampilkan.", "info")
        return redirect(url_for("dashboard_user"))

    # BMI status color mapping for UI
    color_map = {
        "Kurus": {"bg": "blue", "icon": "📉", "badge": "bg-blue-100 text-blue-800"},
        "Normal": {"bg": "green", "icon": "✅", "badge": "bg-green-100 text-green-800"},
        "Overweight": {
            "bg": "yellow",
            "icon": "⚠️",
            "badge": "bg-yellow-100 text-yellow-800",
        },
        "Obesitas I": {
            "bg": "orange",
            "icon": "🔶",
            "badge": "bg-orange-100 text-orange-800",
        },
        "Obesitas II": {"bg": "red", "icon": "🔴", "badge": "bg-red-100 text-red-800"},
    }
    result["color_info"] = color_map.get(result["kategori_imt"], color_map["Normal"])

    return render_template("hasil_konsultasi.html", result=result)


@app.route("/hasil/<int:konsultasi_id>")
@login_required
def hasil_by_id(konsultasi_id):
    """Display a historical consultation result by ID."""
    user_id = session["user_id"]

    # Fetch consultation — ensure it belongs to the current user (or admin can view all)
    if session.get("role") == "admin":
        rec = query_db(
            "SELECT * FROM consultation WHERE id_konsultasi = %s LIMIT 1",
            (konsultasi_id,),
            one=True,
        )
    else:
        rec = query_db(
            "SELECT * FROM consultation WHERE id_konsultasi = %s AND id_user = %s LIMIT 1",
            (konsultasi_id, user_id),
            one=True,
        )

    if not rec:
        flash("Hasil konsultasi tidak ditemukan.", "danger")
        return redirect(url_for("dashboard_user"))

    # Fetch deskripsi_status from knowledge_base
    kb = query_db(
        "SELECT deskripsi_status FROM knowledge_base WHERE kategori_imt = %s AND aktivitas = %s LIMIT 1",
        (rec["kategori_imt"], rec["aktivitas"]),
        one=True,
    )

    color_map = {
        "Kurus": {"bg": "blue", "icon": "📉", "badge": "bg-blue-100 text-blue-800"},
        "Normal": {"bg": "green", "icon": "✅", "badge": "bg-green-100 text-green-800"},
        "Overweight": {
            "bg": "yellow",
            "icon": "⚠️",
            "badge": "bg-yellow-100 text-yellow-800",
        },
        "Obesitas I": {
            "bg": "orange",
            "icon": "🔶",
            "badge": "bg-orange-100 text-orange-800",
        },
        "Obesitas II": {"bg": "red", "icon": "🔴", "badge": "bg-red-100 text-red-800"},
    }

    result = {
        "id": rec["id_konsultasi"],
        "nama_pasien": session.get("nama", "-"),
        "berat_badan": rec["berat_badan"],
        "tinggi_badan": rec["tinggi_badan"],
        "usia": rec["usia"],
        "aktivitas": rec["aktivitas"],
        "nilai_imt": rec["nilai_imt"],
        "kategori_imt": rec["kategori_imt"],
        "status_gizi": rec["status_gizi"],
        "deskripsi_status": kb["deskripsi_status"] if kb else "",
        "rekomendasi_diet": rec["rekomendasi_diet"],
        "target_kalori": rec["target_kalori"],
        "tanggal": rec["tanggal_konsultasi"].strftime("%d %B %Y, %H:%M")
        if hasattr(rec["tanggal_konsultasi"], "strftime")
        else str(rec["tanggal_konsultasi"]),
        "color_info": color_map.get(rec["kategori_imt"], color_map["Normal"]),
    }

    return render_template("hasil_konsultasi.html", result=result)


# ============================================================
# ADMIN ROUTES — Knowledge Base CRUD
# ============================================================
@app.route("/admin/dashboard")
@admin_required
def dashboard_admin():
    """
    Admin dashboard.
    Displays all knowledge base rules with Edit/Delete actions
    and a form to add new rules.
    """
    # Fetch all rules ordered by BMI category then activity
    rules = query_db(
        """
        SELECT id_rule, kategori_imt, aktivitas,
               rekomendasi_diet, target_kalori, deskripsi_status
        FROM knowledge_base
        ORDER BY
            FIELD(kategori_imt, 'Kurus', 'Normal', 'Overweight', 'Obesitas I', 'Obesitas II'),
            FIELD(aktivitas, 'Sedentari', 'Ringan', 'Sedang', 'Berat')
        """
    )

    # Statistics for dashboard cards
    total_rules = len(rules) if rules else 0
    total_users = query_db(
        'SELECT COUNT(*) AS cnt FROM `user` WHERE role = "user"', one=True
    )["cnt"]
    total_consults = query_db("SELECT COUNT(*) AS cnt FROM consultation", one=True)[
        "cnt"
    ]
    recent_consults = query_db(
        """
        SELECT c.id_konsultasi, u.nama, c.nilai_imt, c.kategori_imt,
               DATE_FORMAT(c.tanggal_konsultasi, '%%d/%%m/%%Y %%H:%%i') AS tgl
        FROM consultation c
        JOIN `user` u ON c.id_user = u.id_user
        ORDER BY c.tanggal_konsultasi DESC
        LIMIT 8
        """
    )

    imt_categories = ["Kurus", "Normal", "Overweight", "Obesitas I", "Obesitas II"]
    activity_levels = ["Sedentari", "Ringan", "Sedang", "Berat"]

    return render_template(
        "dashboard_admin.html",
        rules=rules,
        imt_categories=imt_categories,
        activity_levels=activity_levels,
        total_rules=total_rules,
        total_users=total_users,
        total_consults=total_consults,
        recent_consults=recent_consults,
    )


@app.route("/admin/rule/add", methods=["POST"])
@admin_required
def add_rule():
    """Add a new IF-THEN rule to the knowledge base."""
    kategori_imt = request.form.get("kategori_imt", "").strip()
    aktivitas = request.form.get("aktivitas", "").strip()
    rekomendasi_diet = request.form.get("rekomendasi_diet", "").strip()
    target_kalori_s = request.form.get("target_kalori", "").strip()
    deskripsi_status = request.form.get("deskripsi_status", "").strip()

    # Validation
    valid_imt = ["Kurus", "Normal", "Overweight", "Obesitas I", "Obesitas II"]
    valid_act = ["Sedentari", "Ringan", "Sedang", "Berat"]
    errors = []

    if kategori_imt not in valid_imt:
        errors.append("Kategori IMT tidak valid.")
    if aktivitas not in valid_act:
        errors.append("Tingkat aktivitas tidak valid.")
    if not rekomendasi_diet:
        errors.append("Rekomendasi diet tidak boleh kosong.")
    if not target_kalori_s:
        errors.append("Target kalori tidak boleh kosong.")

    target_kalori = None
    if target_kalori_s:
        try:
            target_kalori = int(target_kalori_s)
            if target_kalori <= 0 or target_kalori > 10000:
                errors.append("Target kalori harus antara 1 dan 10000 kkal.")
        except ValueError:
            errors.append("Target kalori harus berupa angka bulat.")

    if not errors:
        # Check for duplicate rule
        existing = query_db(
            "SELECT id_rule FROM knowledge_base WHERE kategori_imt = %s AND aktivitas = %s LIMIT 1",
            (kategori_imt, aktivitas),
            one=True,
        )
        if existing:
            errors.append(
                f'Aturan untuk kombinasi "{kategori_imt}" + "{aktivitas}" sudah ada. '
                "Gunakan fitur Edit untuk mengubahnya."
            )

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("dashboard_admin"))

    query_db(
        """
        INSERT INTO knowledge_base
            (kategori_imt, aktivitas, rekomendasi_diet, target_kalori, deskripsi_status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (kategori_imt, aktivitas, rekomendasi_diet, target_kalori, deskripsi_status),
        commit=True,
    )
    flash(
        f'Aturan baru "{kategori_imt} + {aktivitas}" berhasil ditambahkan.', "success"
    )
    return redirect(url_for("dashboard_admin"))


@app.route("/admin/rule/edit/<int:rule_id>", methods=["GET", "POST"])
@admin_required
def edit_rule(rule_id):
    """
    Edit an existing rule in the knowledge base.
    GET  : Show pre-filled edit form
    POST : Validate and update the rule
    """
    rule = query_db(
        "SELECT * FROM knowledge_base WHERE id_rule = %s LIMIT 1", (rule_id,), one=True
    )
    if not rule:
        flash("Aturan tidak ditemukan.", "danger")
        return redirect(url_for("dashboard_admin"))

    valid_imt = ["Kurus", "Normal", "Overweight", "Obesitas I", "Obesitas II"]
    valid_act = ["Sedentari", "Ringan", "Sedang", "Berat"]

    if request.method == "POST":
        kategori_imt = request.form.get("kategori_imt", "").strip()
        aktivitas = request.form.get("aktivitas", "").strip()
        rekomendasi_diet = request.form.get("rekomendasi_diet", "").strip()
        target_kalori_s = request.form.get("target_kalori", "").strip()
        deskripsi_status = request.form.get("deskripsi_status", "").strip()

        errors = []
        if kategori_imt not in valid_imt:
            errors.append("Kategori IMT tidak valid.")
        if aktivitas not in valid_act:
            errors.append("Tingkat aktivitas tidak valid.")
        if not rekomendasi_diet:
            errors.append("Rekomendasi diet tidak boleh kosong.")

        target_kalori = None
        if target_kalori_s:
            try:
                target_kalori = int(target_kalori_s)
                if target_kalori <= 0 or target_kalori > 10000:
                    errors.append("Target kalori harus antara 1 dan 10000 kkal.")
            except ValueError:
                errors.append("Target kalori harus berupa angka bulat.")
        else:
            errors.append("Target kalori tidak boleh kosong.")

        # Check for duplicate (excluding current rule)
        if not errors:
            duplicate = query_db(
                """
                SELECT id_rule FROM knowledge_base
                WHERE kategori_imt = %s AND aktivitas = %s AND id_rule != %s
                LIMIT 1
                """,
                (kategori_imt, aktivitas, rule_id),
                one=True,
            )
            if duplicate:
                errors.append(
                    f'Aturan untuk "{kategori_imt}" + "{aktivitas}" sudah ada pada aturan lain.'
                )

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "edit_rule.html",
                rule=rule,
                imt_categories=valid_imt,
                activity_levels=valid_act,
            )

        query_db(
            """
            UPDATE knowledge_base
            SET kategori_imt = %s, aktivitas = %s,
                rekomendasi_diet = %s, target_kalori = %s, deskripsi_status = %s
            WHERE id_rule = %s
            """,
            (
                kategori_imt,
                aktivitas,
                rekomendasi_diet,
                target_kalori,
                deskripsi_status,
                rule_id,
            ),
            commit=True,
        )
        flash(f"Aturan ID #{rule_id} berhasil diperbarui.", "success")
        return redirect(url_for("dashboard_admin"))

    return render_template(
        "edit_rule.html", rule=rule, imt_categories=valid_imt, activity_levels=valid_act
    )


@app.route("/admin/rule/delete/<int:rule_id>", methods=["POST"])
@admin_required
def delete_rule(rule_id):
    """Delete a rule from the knowledge base."""
    rule = query_db(
        "SELECT id_rule, kategori_imt, aktivitas FROM knowledge_base WHERE id_rule = %s LIMIT 1",
        (rule_id,),
        one=True,
    )
    if not rule:
        flash("Aturan tidak ditemukan.", "danger")
        return redirect(url_for("dashboard_admin"))

    query_db("DELETE FROM knowledge_base WHERE id_rule = %s", (rule_id,), commit=True)
    flash(
        f"Aturan #{rule_id} ({rule['kategori_imt']} + {rule['aktivitas']}) berhasil dihapus.",
        "success",
    )
    return redirect(url_for("dashboard_admin"))


@app.route("/admin/rule/view/<int:rule_id>")
@admin_required
def view_rule(rule_id):
    """API endpoint: Return a single rule as JSON (for AJAX modal editing)."""
    rule = query_db(
        "SELECT * FROM knowledge_base WHERE id_rule = %s LIMIT 1", (rule_id,), one=True
    )
    if not rule:
        return jsonify({"error": "Aturan tidak ditemukan"}), 404
    return jsonify(rule)


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ============================================================
# UTILITY: Create admin account on first run
# ============================================================
def create_default_admin():
    """
    Creates the default admin account if it doesn't already exist.
    Called on application startup.
    Default credentials: admin / admin123
    """
    try:
        existing = query_db(
            'SELECT id_user FROM `user` WHERE username = "admin" LIMIT 1', one=True
        )
        if not existing:
            hashed = generate_password_hash("admin123")
            query_db(
                "INSERT INTO `user` (nama, username, password, role) VALUES (%s, %s, %s, %s)",
                ("Administrator", "admin", hashed, "admin"),
                commit=True,
            )
            print("[INIT] Default admin account created: admin / admin123")
        else:
            print("[INIT] Admin account already exists.")
    except Exception as exc:
        print(f"[INIT] Could not create admin: {exc}")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    with app.app_context():
        try:
            create_default_admin()
        except Exception as e:
            print(f"[WARN] Skipping admin creation (DB may not be ready): {e}")
    app.run(debug=True, host="0.0.0.0", port=5000)
