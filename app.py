from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    session,
    send_file,
    abort
)

from functools import wraps
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    LargeBinary,
    Text
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)

from sqlalchemy.exc import IntegrityError

import qrcode
import os
import uuid
import io


# ============================================================
# إعداد Flask
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-SECRET-KEY-123456789"
)


# ============================================================
# إعداد قاعدة البيانات
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL")


# Render أحيانًا يعطي الرابط بالشكل postgres://
# SQLAlchemy الحديثة تحتاج postgresql://
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

else:
    # للاختبار المحلي فقط
    engine = create_engine(
        "sqlite:///people.db",
        connect_args={
            "check_same_thread": False
        }
    )


SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


# ============================================================
# نموذج الأشخاص
# ============================================================

class Person(Base):

    __tablename__ = "people"

    id = Column(
        String(32),
        primary_key=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    rank = Column(
        String(200),
        nullable=False
    )

    military_number = Column(
        String(200),
        nullable=False
    )

    blood_type = Column(
        String(100),
        nullable=True
    )

    national_id = Column(
        String(200),
        nullable=True
    )

    department = Column(
        String(200),
        nullable=True
    )

    photo_data = Column(
        LargeBinary,
        nullable=True
    )

    photo_mimetype = Column(
        String(100),
        nullable=True
    )

    qr_data = Column(
        LargeBinary,
        nullable=True
    )


# ============================================================
# نموذج المستخدمين
# ============================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        Text,
        nullable=False
    )


# ============================================================
# إنشاء الجداول
# ============================================================

def init_database():

    Base.metadata.create_all(
        engine
    )

    db = SessionLocal()

    try:
        admin = (
            db.query(User)
            .filter_by(username="admin")
            .first()
        )

        admin_password = os.environ.get("ADMIN_PASSWORD")

if not admin_password:
    raise RuntimeError("ADMIN_PASSWORD environment variable is not set")

        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash(
                    admin_password
                )
            )
            db.add(admin)

        else:
            admin.password_hash = generate_password_hash(
                admin_password
            )

        db.commit()

    finally:
        db.close()

# ============================================================
# حماية الصفحات
# ============================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped_view


# ============================================================
# تسجيل الدخول
# ============================================================

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

        db = SessionLocal()

        try:

            user = (
                db.query(User)
                .filter_by(username=username)
                .first()
            )

            if user and check_password_hash(
                user.password_hash,
                password
            ):

                session.clear()

                session["user_id"] = user.id

                session["username"] = user.username

                return redirect(
                    url_for("home")
                )

        finally:

            db.close()

        return """
        <!DOCTYPE html>

        <html lang="ar" dir="rtl">

        <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <title>خطأ في تسجيل الدخول</title>

        <style>

        body {
            font-family: Arial;
            background: #f3f3f3;
            padding: 30px;
        }

        .box {
            max-width: 450px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
        }

        a {
            color: #222;
        }

        </style>

        </head>

        <body>

        <div class="box">

        <h3>
        اسم المستخدم أو كلمة المرور غير صحيحة
        </h3>

        <a href="/login">
        العودة إلى تسجيل الدخول
        </a>

        </div>

        </body>

        </html>
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

* {
    box-sizing: border-box;
}

body {

    font-family: Arial, sans-serif;

    background: #f3f3f3;

    padding: 30px;

}

.box {

    max-width: 430px;

    margin: 60px auto;

    background: white;

    padding: 30px;

    border-radius: 15px;

    box-shadow: 0 3px 15px rgba(0,0,0,.10);

}

h2 {

    text-align: center;

    margin-bottom: 25px;

}

label {

    display: block;

    margin-bottom: 7px;

    font-weight: bold;

}

input {

    width: 100%;

    padding: 13px;

    margin-bottom: 18px;

    border: 1px solid #ccc;

    border-radius: 8px;

    font-size: 16px;

}

button {

    width: 100%;

    padding: 14px;

    background: #222;

    color: white;

    border: none;

    border-radius: 8px;

    font-size: 17px;

    cursor: pointer;

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
    autocomplete="username"
    required
>

<label>
كلمة المرور
</label>

<input
    type="password"
    name="password"
    autocomplete="current-password"
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


# ============================================================
# لوحة الإدارة
# ============================================================
@app.route("/health")
def health():
    return "OK", 200



 
@app.route("/")
@login_required
def home():

    db = SessionLocal()

    try:

        people = (
            db.query(Person)
            .order_by(Person.id.desc())
            .all()
        )

    finally:

        db.close()

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
لوحة إدارة الأشخاص
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
    placeholder="ابحث بالاسم أو النمرة العسكرية أو الرتبة..."
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
    data-search="{{ person.name }} {{ person.military_number }} {{ person.rank }} {{ person.department or '' }}"
>

<img
    class="photo"
    src="/photo/{{ person.id }}"
    alt="صورة {{ person.name }}"
>

<div class="name">
{{ person.name }}
</div>

<div class="info">
<strong>الرتبة:</strong>
{{ person.rank }}
</div>

<div class="info">
<strong>النمرة:</strong>
{{ person.military_number }}
</div>

<div class="info">
<strong>الجهة:</strong>
{{ person.department or '' }}
</div>

<div class="buttons">

<a
    class="small-btn qr-btn"
    href="/qr/{{ person.id }}"
    target="_blank"
>
عرض QR
</a>

<a
    class="small-btn"
    href="/person/{{ person.id }}"
    target="_blank"
>
عرض البيانات
</a>

<a
    class="small-btn"
    href="/edit/{{ person.id }}"
>
تعديل
</a>

<form
    method="POST"
    action="/delete/{{ person.id }}"
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

    const input =
        document
        .getElementById("search")
        .value
        .toLowerCase();

    const cards =
        document
        .querySelectorAll(".person-card");

    cards.forEach(function(card) {

        const text =
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


# ============================================================
# إضافة شخص
# ============================================================

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
إضافة شخص جديد
</title>

<style>

* {
    box-sizing: border-box;
}

body {

    font-family: Arial;

    background: #f3f3f3;

    padding: 20px;

}

.box {

    max-width: 600px;

    margin: auto;

    background: white;

    padding: 25px;

    border-radius: 15px;

    box-shadow: 0 3px 15px rgba(0,0,0,.10);

}

h2 {

    margin-top: 0;

}

label {

    display: block;

    margin-bottom: 7px;

    font-weight: bold;

}

input {

    width: 100%;

    padding: 12px;

    margin: 7px 0 17px;

    border: 1px solid #ccc;

    border-radius: 8px;

    font-size: 16px;

}

button {

    width: 100%;

    padding: 14px;

    background: #222;

    color: white;

    border: none;

    border-radius: 8px;

    font-size: 16px;

}

.back {

    display: block;

    margin-top: 18px;

    text-align: center;

    color: #222;

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

<label>
الإسم:
</label>

<input
    type="text"
    name="name"
    required
>

<label>
الرتبة:
</label>

<input
    type="text"
    name="rank"
    required
>

<label>
النمرة العسكرية:
</label>

<input
    type="text"
    name="military_number"
    required
>

<label>
فصيلة الدم:
</label>

<input
    type="text"
    name="blood_type"
>

<label>
الرقم الوطني:
</label>

<input
    type="text"
    name="national_id"
>

<label>
الجهة:
</label>

<input
    type="text"
    name="department"
>

<label>
الصورة الشخصية:
</label>

<input
    type="file"
    name="photo"
    accept="image/jpeg,image/png,image/webp"
    required
>

<button type="submit">
إنشاء QR Code
</button>

</form>

<a
    href="/"
    class="back"
>
← العودة إلى لوحة الإدارة
</a>

</div>

</body>

</html>

"""


# ============================================================
# إنشاء الشخص و QR
# ============================================================

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

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if photo.mimetype not in allowed_types:

        return (
            "نوع الصورة غير مدعوم. استخدم JPG أو PNG أو WEBP.",
            400
        )

    photo_bytes = photo.read()

    if not photo_bytes:

        return (
            "الصورة فارغة",
            400
        )

    # حد أقصى 5 ميجابايت
    if len(photo_bytes) > 5 * 1024 * 1024:

        return (
            "حجم الصورة كبير جدًا. الحد الأقصى 5 ميجابايت.",
            400
        )

    person_id = uuid.uuid4().hex

    # --------------------------------------------------------
    # إنشاء رابط الشخص
    # --------------------------------------------------------

    person_url = url_for(
        "person",
        person_id=person_id,
        _external=True
    )

    # --------------------------------------------------------
    # إنشاء QR
    # --------------------------------------------------------

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

    qr_buffer = io.BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG"
    )

    qr_bytes = qr_buffer.getvalue()

    # --------------------------------------------------------
    # حفظ البيانات في قاعدة البيانات
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        person = Person(
            id=person_id,
            name=name,
            rank=rank,
            military_number=military_number,
            blood_type=blood_type,
            national_id=national_id,
            department=department,
            photo_data=photo_bytes,
            photo_mimetype=photo.mimetype,
            qr_data=qr_bytes
        )

        db.add(person)

        db.commit()

    except Exception:

        db.rollback()

        return (
            "حدث خطأ أثناء حفظ البيانات",
            500
        )

    finally:

        db.close()

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
تم إنشاء QR
</title>

<style>

body {

    font-family: Arial;

    background: #f3f3f3;

    padding: 25px;

    text-align: center;

}

.box {

    max-width: 600px;

    margin: auto;

    background: white;

    padding: 30px;

    border-radius: 15px;

}

.qr {

    width: 300px;

    max-width: 100%;

    margin: 20px auto;

}

a {

    display: block;

    margin: 14px;

    color: #222;

}

</style>

</head>

<body>

<div class="box">

<h2>
تم إنشاء QR Code بنجاح ✅
</h2>

<p>
يمكن الآن مسح هذا الكود من أي هاتف.
</p>

<img
    class="qr"
    src="/qr/{{ person_id }}"
>

<br>

<a
    href="/person/{{ person_id }}"
    target="_blank"
>
فتح بيانات الشخص
</a>

<a href="/">
العودة إلى لوحة الإدارة
</a>

</div>

</body>

</html>

""", person_id=person_id)


# ============================================================
# عرض الصورة
# ============================================================

@app.route(
    "/photo/<person_id>"
)
def photo(person_id):

    db = SessionLocal()

    try:

        person = (
            db.query(Person)
            .filter_by(id=person_id)
            .first()
        )

        if not person or not person.photo_data:

            abort(404)

        return send_file(
            io.BytesIO(person.photo_data),
            mimetype=person.photo_mimetype or "image/jpeg"
        )

    finally:

        db.close()


# ============================================================
# عرض QR
# ============================================================

@app.route(
    "/qr/<person_id>"
)
def qr(person_id):

    db = SessionLocal()

    try:

        person = (
            db.query(Person)
            .filter_by(id=person_id)
            .first()
        )

        if not person or not person.qr_data:

            abort(404)

        return send_file(
            io.BytesIO(person.qr_data),
            mimetype="image/png"
        )

    finally:

        db.close()


# ============================================================
# تعديل شخص
# ============================================================

@app.route(
    "/edit/<person_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_person(person_id):

    db = SessionLocal()

    try:

        person = (
            db.query(Person)
            .filter_by(id=person_id)
            .first()
        )

        if not person:

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

            person.name = name

            person.rank = rank

            person.military_number = military_number

            person.blood_type = blood_type

            person.national_id = national_id

            person.department = department

            # ------------------------------------------------
            # تغيير الصورة اختياري
            # ------------------------------------------------

            new_photo = request.files.get(
                "photo"
            )

            if new_photo and new_photo.filename:

                allowed_types = {
                    "image/jpeg",
                    "image/png",
                    "image/webp"
                }

                if new_photo.mimetype not in allowed_types:

                    return (
                        "نوع الصورة غير مدعوم",
                        400
                    )

                new_photo_bytes = new_photo.read()

                if len(new_photo_bytes) > 5 * 1024 * 1024:

                    return (
                        "حجم الصورة كبير جدًا. الحد الأقصى 5 ميجابايت.",
                        400
                    )

                person.photo_data = new_photo_bytes

                person.photo_mimetype = new_photo.mimetype

            db.commit()

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

* {
    box-sizing: border-box;
}

body {

    font-family: Arial;

    background: #f3f3f3;

    padding: 20px;

}

.box {

    max-width: 600px;

    margin: auto;

    background: white;

    padding: 25px;

    border-radius: 15px;

}

.photo {

    display: block;

    width: 160px;

    height: 190px;

    object-fit: cover;

    margin: 15px auto 25px;

    border-radius: 10px;

}

label {

    display: block;

    font-weight: bold;

    margin-bottom: 7px;

}

input {

    width: 100%;

    padding: 12px;

    margin: 7px 0 17px;

    border: 1px solid #ccc;

    border-radius: 8px;

    font-size: 16px;

}

button {

    width: 100%;

    padding: 14px;

    background: #222;

    color: white;

    border: none;

    border-radius: 8px;

    font-size: 16px;

}

.back {

    display: block;

    text-align: center;

    margin-top: 18px;

    color: #222;

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
    src="/photo/{{ person.id }}"
>

<form
    method="POST"
    enctype="multipart/form-data"
>

<label>
الإسم:
</label>

<input
    name="name"
    value="{{ person.name }}"
    required
>

<label>
الرتبة:
</label>

<input
    name="rank"
    value="{{ person.rank }}"
    required
>

<label>
النمرة العسكرية:
</label>

<input
    name="military_number"
    value="{{ person.military_number }}"
    required
>

<label>
فصيلة الدم:
</label>

<input
    name="blood_type"
    value="{{ person.blood_type or '' }}"
>

<label>
الرقم الوطني:
</label>

<input
    name="national_id"
    value="{{ person.national_id or '' }}"
>

<label>
الجهة:
</label>

<input
    name="department"
    value="{{ person.department or '' }}"
>

<label>
تغيير الصورة الشخصية - اختياري:
</label>

<input
    type="file"
    name="photo"
    accept="image/jpeg,image/png,image/webp"
>

<button type="submit">
حفظ التعديلات
</button>

</form>

<a
    href="/"
    class="back"
>
← العودة إلى لوحة الإدارة
</a>

</div>

</body>

</html>

""", person=person)

    finally:

        db.close()


# ============================================================
# حذف شخص
# ============================================================

@app.route(
    "/delete/<person_id>",
    methods=["POST"]
)
@login_required
def delete_person(person_id):

    db = SessionLocal()

    try:

        person = (
            db.query(Person)
            .filter_by(id=person_id)
            .first()
        )

        if not person:

            return (
                "الشخص غير موجود",
                404
            )

        db.delete(person)

        db.commit()

        return redirect(
            url_for("home")
        )

    finally:

        db.close()


# ============================================================
# عرض بيانات الشخص بواسطة QR
# ============================================================

@app.route(
    "/person/<person_id>"
)
def person(person_id):

    db = SessionLocal()

    try:

        person_data = (
            db.query(Person)
            .filter_by(id=person_id)
            .first()
        )

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

* {
    box-sizing: border-box;
}

body {

    font-family: Arial, sans-serif;

    margin: 0;

    padding: 20px;

    background: #f5f5f5;

    color: #222;

}

.container {

    max-width: 520px;

    margin: 20px auto;

    background: white;

    padding: 25px;

    border-radius: 16px;

    box-shadow: 0 3px 15px rgba(0,0,0,.10);

}

.header {

    text-align: center;

    margin-bottom: 20px;

}

.header h2 {

    margin: 5px 0;

}

.header p {

    margin: 7px 0;

    color: #666;

}

.photo {

    display: block;

    width: 190px;

    height: 230px;

    object-fit: cover;

    margin: 0 auto 25px;

    border-radius: 10px;

}

.row {

    padding: 13px 0;

    border-bottom: 1px solid #ddd;

    font-size: 17px;

}

.title {

    font-weight: bold;

}

</style>

</head>

<body>

<div class="container">

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
    src="/photo/{{ person_data.id }}"
    alt="صورة {{ person_data.name }}"
>

<div class="row">

<span class="title">
الإسم:
</span>

{{ person_data.name }}

</div>

<div class="row">

<span class="title">
الرتبة:
</span>

{{ person_data.rank }}

</div>

<div class="row">

<span class="title">
النمرة العسكرية:
</span>

{{ person_data.military_number }}

</div>

<div class="row">

<span class="title">
فصيلة الدم:
</span>

{{ person_data.blood_type or '' }}

</div>

<div class="row">

<span class="title">
الرقم الوطني:
</span>

{{ person_data.national_id or '' }}

</div>

<div class="row">

<span class="title">
الجهة:
</span>

{{ person_data.department or '' }}

</div>

</div>

</body>

</html>

""", person_data=person_data)

    finally:

        db.close()


# ============================================================
# تسجيل الخروج
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# تهيئة قاعدة البيانات
# ============================================================

init_database()


# ============================================================
# تشغيل البرنامج
# ============================================================

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
