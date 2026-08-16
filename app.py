from flask import (
    Flask,
    render_template_string,
    request,
    send_from_directory,
    redirect,
    url_for,
    session
)

from functools import wraps
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.middleware.proxy_fix import ProxyFix

import sqlite3
import qrcode
import os
import uuid


# ==================================================
# إعداد Flask
# ==================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-SECRET-KEY"
)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1,
    x_prefix=1
)


# ==================================================
# إعدادات المشروع
# ==================================================

DATA_DIR = os.environ.get("DATA_DIR", ".")

DATABASE = os.path.join(
    DATA_DIR,
    "people.db"
)

UPLOAD_FOLDER = os.path.join(
    DATA_DIR,
    "uploads"
)

QR_FOLDER = os.path.join(
    DATA_DIR,
    "qr_codes"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)


# ==================================================
# حماية الصفحات
# ==================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return view(*args, **kwargs)

    return wrapped_view


# ==================================================
# إنشاء قاعدة البيانات
# ==================================================

def init_database():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS people (

            id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            rank TEXT NOT NULL,

            military_number TEXT NOT NULL,

            blood_type TEXT,

            national_id TEXT,

            department TEXT,

            photo TEXT,

            qr_file TEXT

        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL

        )
    """)

    admin = conn.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    ).fetchone()

    if not admin:

        password_hash = generate_password_hash(
            "admin123"
        )

        conn.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES (?, ?)
            """,
            (
                "admin",
                password_hash
            )
        )

    conn.commit()

    conn.close()


# ==================================================
# تسجيل الدخول
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = sqlite3.connect(
            DATABASE
        )

        conn.row_factory = sqlite3.Row

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            return redirect(
                url_for("home")
            )

        return """
        <div
            style="
            text-align:center;
            font-family:Arial;
            padding:40px;
            "
        >

            <h3>
                اسم المستخدم أو كلمة المرور غير صحيحة
            </h3>

            <a href="/login">
                العودة
            </a>

        </div>
        """, 401

    return """

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
تسجيل الدخول
</title>

<style>

body {

    font-family: Arial;

    background: #f5f5f5;

    padding: 30px;

}

.box {

    max-width: 400px;

    margin: auto;

    background: white;

    padding: 30px;

    border-radius: 12px;

    box-shadow: 0 2px 10px #ccc;

}

input {

    width: 100%;

    padding: 12px;

    margin: 8px 0 15px;

    box-sizing: border-box;

}

button {

    width: 100%;

    padding: 13px;

    background: #222;

    color: white;

    border: none;

    border-radius: 6px;

    font-size: 16px;

}

</style>

</head>

<body>

<div class="box">

<h2>
تسجيل الدخول
</h2>

<form method="POST">

<label>
اسم المستخدم
</label>

<input
    type="text"
    name="username"
    required
>

<label>
كلمة المرور
</label>

<input
    type="password"
    name="password"
    required
>

<button type="submit">
دخول
</button>

</form>

</div>

</body>

</html>

"""


# ==================================================
# لوحة الإدارة
# ==================================================

@app.route("/")
@login_required
def home():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    people = conn.execute(
        """
        SELECT *
        FROM people
        ORDER BY rowid DESC
        """
    ).fetchall()

    conn.close()

    return render_template_string("""

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
لوحة الإدارة
</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family: Arial, sans-serif;

    background: #f3f3f3;

    color: #222;

}

.container {

    max-width: 1100px;

    margin: auto;

    padding: 20px;

}

.header {

    background: white;

    padding: 22px;

    border-radius: 15px;

    box-shadow: 0 3px 12px rgba(0,0,0,.10);

    margin-bottom: 20px;

}

.header h1 {

    margin: 0 0 8px;

}

.header p {

    margin: 0;

    color: #666;

}

.actions {

    margin-top: 18px;

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

}

.btn {

    display: inline-block;

    padding: 12px 18px;

    border-radius: 8px;

    text-decoration: none;

}

.btn-add {

    background: #222;

    color: white;

}

.btn-logout {

    background: #eee;

    color: #222;

}

.search {

    width: 100%;

    padding: 13px;

    border: 1px solid #ccc;

    border-radius: 8px;

    margin-bottom: 20px;

    font-size: 16px;

}

.count {

    margin-bottom: 15px;

    font-weight: bold;

}

.grid {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(280px, 1fr));

    gap: 18px;

}

.card {

    background: white;

    border-radius: 15px;

    padding: 18px;

    box-shadow: 0 3px 12px rgba(0,0,0,.10);

}

.photo {

    display: block;

    width: 130px;

    height: 160px;

    object-fit: cover;

    border-radius: 10px;

    margin: 0 auto 15px;

}

.name {

    text-align: center;

    font-size: 20px;

    font-weight: bold;

    margin-bottom: 12px;

}

.info {

    padding: 8px 0;

    border-bottom: 1px solid #eee;

}

.buttons {

    display: grid;

    grid-template-columns: 1fr 1fr;

    gap: 8px;

    margin-top: 15px;

}

.small-btn {

    display: block;

    text-align: center;

    padding: 10px;

    border-radius: 7px;

    text-decoration: none;

    background: #eee;

    color: #222;

}

.qr-btn {

    background: #222;

    color: white;

}

.delete-btn {

    background: #b00020;

    color: white;

    border: none;

    width: 100%;

    padding: 10px;

    border-radius: 7px;

    cursor: pointer;

}

.empty {

    background: white;

    padding: 40px;

    text-align: center;

    border-radius: 15px;

}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>
لوحة إدارة الأشخاص
</h1>

<p>
مرحبًا {{ session["username"] }}
</p>

<div class="actions">

<a
    href="/add"
    class="btn btn-add"
>
+ إضافة شخص جديد
</a>

<a
    href="/logout"
    class="btn btn-logout"
>
تسجيل الخروج
</a>

</div>

</div>

<input
    type="text"
    id="search"
    class="search"
    placeholder="ابحث بالاسم أو النمرة العسكرية..."
    onkeyup="searchPeople()"
>

<div class="count">

عدد الأشخاص:
{{ people|length }}

</div>

{% if people %}

<div class="grid">

{% for person in people %}

<div
    class="card person-card"
    data-search="
        {{ person['name'] }}
        {{ person['military_number'] }}
        {{ person['rank'] }}
    "
>

<img
    class="photo"
    src="/uploads/{{ person['photo'] }}"
>

<div class="name">
{{ person['name'] }}
</div>

<div class="info">
<strong>الرتبة:</strong>
{{ person['rank'] }}
</div>

<div class="info">
<strong>النمرة:</strong>
{{ person['military_number'] }}
</div>

<div class="info">
<strong>الجهة:</strong>
{{ person['department'] or '' }}
</div>

<div class="buttons">

<a
    class="small-btn qr-btn"
    href="/qr/{{ person['qr_file'] }}"
    target="_blank"
>
عرض QR
</a>

<a
    class="small-btn"
    href="/person/{{ person['id'] }}"
    target="_blank"
>
عرض البيانات
</a>

<a
    class="small-btn"
    href="/edit/{{ person['id'] }}"
>
تعديل
</a>

<form
    method="POST"
    action="/delete/{{ person['id'] }}"
    onsubmit="return confirm('هل أنت متأكد من حذف هذا الشخص؟');"
>

<button
    type="submit"
    class="delete-btn"
>
حذف
</button>

</form>

</div>

</div>

{% endfor %}

</div>

{% else %}

<div class="empty">

<h3>
لا توجد بيانات حتى الآن
</h3>

<p>
اضغط على "إضافة شخص جديد" لإنشاء أول QR.
</p>

</div>

{% endif %}

</div>

<script>

function searchPeople() {

    let input =
        document
        .getElementById("search")
        .value
        .toLowerCase();

    let cards =
        document
        .querySelectorAll(".person-card");

    cards.forEach(function(card) {

        let text =
            card
            .getAttribute("data-search")
            .toLowerCase();

        card.style.display =
            text.includes(input)
            ? ""
            : "none";

    });

}

</script>

</body>

</html>

""", people=people)


# ==================================================
# إضافة شخص
# ==================================================

@app.route("/add")
@login_required
def add_person():

    return """

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
إضافة شخص
</title>

<style>

body {

    font-family: Arial;

    background: #f3f3f3;

    padding: 20px;

}

.box {

    max-width: 550px;

    margin: auto;

    background: white;

    padding: 25px;

    border-radius: 15px;

}

input {

    width: 100%;

    padding: 12px;

    margin: 7px 0 16px;

    box-sizing: border-box;

}

button {

    width: 100%;

    padding: 13px;

    background: #222;

    color: white;

    border: none;

    border-radius: 7px;

}

</style>

</head>

<body>

<div class="box">

<h2>
إضافة بيانات شخص جديد
</h2>

<form
    method="POST"
    action="/create"
    enctype="multipart/form-data"
>

<label>الإسم:</label>

<input
    type="text"
    name="name"
    required
>

<label>الرتبة:</label>

<input
    type="text"
    name="rank"
    required
>

<label>النمرة العسكرية:</label>

<input
    type="text"
    name="military_number"
    required
>

<label>فصيلة الدم:</label>

<input
    type="text"
    name="blood_type"
>

<label>الرقم الوطني:</label>

<input
    type="text"
    name="national_id"
>

<label>الجهة:</label>

<input
    type="text"
    name="department"
>

<label>الصورة الشخصية:</label>

<input
    type="file"
    name="photo"
    accept="image/*"
    required
>

<button type="submit">
إنشاء QR Code
</button>

</form>

<br>

<a href="/">
← العودة إلى لوحة الإدارة
</a>

</div>

</body>

</html>

"""


# ==================================================
# إنشاء الشخص و QR
# ==================================================

@app.route(
    "/create",
    methods=["POST"]
)
@login_required
def create():

    name = request.form.get(
        "name",
        ""
    ).strip()

    rank = request.form.get(
        "rank",
        ""
    ).strip()

    military_number = request.form.get(
        "military_number",
        ""
    ).strip()

    blood_type = request.form.get(
        "blood_type",
        ""
    ).strip()

    national_id = request.form.get(
        "national_id",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    photo = request.files.get(
        "photo"
    )

    if not name or not rank or not military_number:

        return (
            "الاسم والرتبة والنمرة العسكرية مطلوبة",
            400
        )

    if not photo or photo.filename == "":

        return (
            "يجب اختيار صورة",
            400
        )

    extension = os.path.splitext(
        photo.filename
    )[1].lower()

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]

    if extension not in allowed_extensions:

        return (
            "نوع الصورة غير مدعوم",
            400
        )

    person_id = uuid.uuid4().hex[:12]

    photo_filename = (
        person_id + extension
    )

    photo.save(
        os.path.join(
            UPLOAD_FOLDER,
            photo_filename
        )
    )

    # رابط الموقع الحقيقي تلقائيًا
    person_url = url_for(
        "person",
        person_id=person_id,
        _external=True
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(
        person_url
    )

    qr.make(
        fit=True
    )

    qr_image = qr.make_image()

    qr_filename = (
        person_id + ".png"
    )

    qr_image.save(
        os.path.join(
            QR_FOLDER,
            qr_filename
        )
    )

    conn = sqlite3.connect(
        DATABASE
    )

    conn.execute(
        """
        INSERT INTO people
        (
            id,
            name,
            rank,
            military_number,
            blood_type,
            national_id,
            department,
            photo,
            qr_file
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            person_id,
            name,
            rank,
            military_number,
            blood_type,
            national_id,
            department,
            photo_filename,
            qr_filename
        )
    )

    conn.commit()

    conn.close()

    return f"""

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
تم إنشاء QR
</title>

</head>

<body
    style="
    text-align:center;
    font-family:Arial;
    padding:30px;
    "
>

<h2>
تم إنشاء QR Code بنجاح ✅
</h2>

<img
    src="/qr/{qr_filename}"
    width="300"
>

<br><br>

<a
    href="/person/{person_id}"
    target="_blank"
>
فتح البيانات
</a>

<br><br>

<a href="/">
العودة إلى لوحة الإدارة
</a>

</body>

</html>

"""


# ==================================================
# تعديل شخص
# ==================================================

@app.route(
    "/edit/<person_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_person(person_id):

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    person_data = conn.execute(
        """
        SELECT *
        FROM people
        WHERE id = ?
        """,
        (person_id,)
    ).fetchone()

    conn.close()

    if not person_data:

        return (
            "الشخص غير موجود",
            404
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        rank = request.form.get(
            "rank",
            ""
        ).strip()

        military_number = request.form.get(
            "military_number",
            ""
        ).strip()

        blood_type = request.form.get(
            "blood_type",
            ""
        ).strip()

        national_id = request.form.get(
            "national_id",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        if not name or not rank or not military_number:

            return (
                "الاسم والرتبة والنمرة العسكرية مطلوبة",
                400
            )

        conn = sqlite3.connect(
            DATABASE
        )

        conn.execute(
            """
            UPDATE people

            SET
                name = ?,
                rank = ?,
                military_number = ?,
                blood_type = ?,
                national_id = ?,
                department = ?

            WHERE id = ?
            """,
            (
                name,
                rank,
                military_number,
                blood_type,
                national_id,
                department,
                person_id
            )
        )

        conn.commit()

        conn.close()

        return redirect(
            url_for("home")
        )

    return render_template_string("""

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
تعديل البيانات
</title>

<style>

body {

    font-family: Arial;

    background: #f3f3f3;

    padding: 20px;

}

.box {

    max-width: 550px;

    margin: auto;

    background: white;

    padding: 25px;

    border-radius: 15px;

}

input {

    width: 100%;

    padding: 12px;

    margin: 7px 0 16px;

    box-sizing: border-box;

}

button {

    width: 100%;

    padding: 13px;

    background: #222;

    color: white;

    border: none;

    border-radius: 7px;

}

.photo {

    display: block;

    width: 150px;

    height: 180px;

    object-fit: cover;

    margin: 15px auto;

    border-radius: 10px;

}

</style>

</head>

<body>

<div class="box">

<h2>
تعديل بيانات الشخص
</h2>

<img
    class="photo"
    src="/uploads/{{ person_data['photo'] }}"
>

<form method="POST">

<label>الإسم:</label>

<input
    name="name"
    value="{{ person_data['name'] }}"
    required
>

<label>الرتبة:</label>

<input
    name="rank"
    value="{{ person_data['rank'] }}"
    required
>

<label>النمرة العسكرية:</label>

<input
    name="military_number"
    value="{{ person_data['military_number'] }}"
    required
>

<label>فصيلة الدم:</label>

<input
    name="blood_type"
    value="{{ person_data['blood_type'] or '' }}"
>

<label>الرقم الوطني:</label>

<input
    name="national_id"
    value="{{ person_data['national_id'] or '' }}"
>

<label>الجهة:</label>

<input
    name="department"
    value="{{ person_data['department'] or '' }}"
>

<button type="submit">
حفظ التعديلات
</button>

</form>

<br>

<a href="/">
← العودة
</a>

</div>

</body>

</html>

""", person_data=person_data)


# ==================================================
# حذف شخص
# ==================================================

@app.route(
    "/delete/<person_id>",
    methods=["POST"]
)
@login_required
def delete_person(person_id):

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    person_data = conn.execute(
        """
        SELECT *
        FROM people
        WHERE id = ?
        """,
        (person_id,)
    ).fetchone()

    if not person_data:

        conn.close()

        return (
            "الشخص غير موجود",
            404
        )

    photo_path = os.path.join(
        UPLOAD_FOLDER,
        person_data["photo"]
    )

    if os.path.exists(photo_path):

        os.remove(photo_path)

    qr_path = os.path.join(
        QR_FOLDER,
        person_data["qr_file"]
    )

    if os.path.exists(qr_path):

        os.remove(qr_path)

    conn.execute(
        """
        DELETE FROM people
        WHERE id = ?
        """,
        (person_id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("home")
    )


# ==================================================
# عرض بيانات الشخص
# ==================================================

@app.route(
    "/person/<person_id>"
)
def person(person_id):

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    person_data = conn.execute(
        """
        SELECT *
        FROM people
        WHERE id = ?
        """,
        (person_id,)
    ).fetchone()

    conn.close()

    if not person_data:

        return (
            "البيانات غير موجودة",
            404
        )

    return render_template_string("""

<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
بيانات الشخص
</title>

<style>

body {

    font-family: Arial;

    max-width: 500px;

    margin: 30px auto;

    padding: 20px;

    background: white;

    color: #222;

}

.header {

    text-align: center;

    margin-bottom: 20px;

}

.header h2 {

    margin: 5px 0;

}

.header p {

    margin: 5px 0;

    font-weight: bold;

}

.photo {

    display: block;

    width: 180px;

    height: 220px;

    object-fit: cover;

    margin: 0 auto 25px;

    border-radius: 8px;

}

.row {

    padding: 12px 0;

    border-bottom: 1px solid #ddd;

    font-size: 17px;

}

.title {

    font-weight: bold;

}

.website {

    text-align: center;

    margin-top: 30px;

    padding-top: 20px;

    border-top: 1px solid #ddd;

}

.website a {

    color: #222;

    text-decoration: none;

    font-weight: bold;

}

</style>

</head>

<body>

<div class="header">

<h2>
حركة جيش تحرير السودان
</h2>

<p>
التحالف السوداني
</p>

</div>

<img
    class="photo"
    src="/uploads/{{ person_data['photo'] }}"
>

<div class="row">

<span class="title">
الإسم:
</span>

{{ person_data['name'] }}

</div>

<div class="row">

<span class="title">
الرتبة:
</span>

{{ person_data['rank'] }}

</div>

<div class="row">

<span class="title">
النمرة العسكرية:
</span>

{{ person_data['military_number'] }}

</div>

<div class="row">

<span class="title">
فصيلة الدم:
</span>

{{ person_data['blood_type'] or '' }}

</div>

<div class="row">

<span class="title">
الرقم الوطني:
</span>

{{ person_data['national_id'] or '' }}

</div>

<div class="row">

<span class="title">
الجهة:
</span>

{{ person_data['department'] or '' }}

</div>

</body>

</html>

""", person_data=person_data)


# ==================================================
# الصور
# ==================================================

@app.route(
    "/uploads/<filename>"
)
def uploads(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ==================================================
# QR
# ==================================================

@app.route(
    "/qr/<filename>"
)
def qr(filename):

    return send_from_directory(
        QR_FOLDER,
        filename
    )


# ==================================================
# تسجيل الخروج
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# تشغيل البرنامج
# ==================================================

init_database()


if __name__ == "__main__":

    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
