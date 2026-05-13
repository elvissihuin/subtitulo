from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from motor import procesar
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# LIMPIEZA AUTOMÁTICA
# =========================

def limpiar_carpetas_antiguas():
    """Borra carpetas en outputs/ más viejas que 24 horas."""
    ahora = time.time()
    limite = 24 * 3600  # 24 horas en segundos
    outputs_dir = "outputs"
    if os.path.exists(outputs_dir):
        for carpeta in os.listdir(outputs_dir):
            carpeta_path = os.path.join(outputs_dir, carpeta)
            if os.path.isdir(carpeta_path):
                mtime = os.path.getmtime(carpeta_path)
                if ahora - mtime > limite:
                    shutil.rmtree(carpeta_path)
                    print(f"Carpeta eliminada: {carpeta_path}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=limpiar_carpetas_antiguas, trigger="interval", hours=1)
scheduler.start()

# =========================
# PÁGINA PRINCIPAL
# =========================

@app.route("/")
@login_required
def inicio():
    return render_template("index.html")

# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("inicio"))
        flash("Credenciales inválidas")
    return render_template("login.html")

# =========================
# SIGNUP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Usuario ya existe")
            return redirect(url_for("signup"))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("inicio"))
    return render_template("signup.html")

# =========================
# LOGOUT
# =========================

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# PROCESAR VIDEO
# =========================

@app.route("/procesar", methods=["POST"])
@login_required
def procesar_video():
    url = request.form["url"]
    traducir = request.form["traducir"]
    subtitulos = request.form["subtitulos"]

    carpeta_id = procesar(url, traducir, subtitulos)

    if not carpeta_id:
        return """
        <h1>❌ Error procesando video</h1>
        <br>
        <a href='/'>Volver</a>
        """

    archivos = os.listdir(f"outputs/{carpeta_id}")
    html_archivos = ""
    for archivo in archivos:
        html_archivos += f"""
        <li>
            <a href="/downloads/{carpeta_id}/{archivo}">{archivo}</a>
        </li>
        """

    return f"""
    <html>
    <head>
        <title>Descargas</title>
        <style>
            body{{background:#0f172a;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}}
            .box{{background:#111827;padding:40px;border-radius:20px;width:600px;}}
            a{{color:#60a5fa;text-decoration:none;font-size:18px;}}
            li{{margin-bottom:15px;}}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>✅ Archivos generados</h1>
            <ul>{html_archivos}</ul>
            <br>
            <a href='/'>🔙 Volver</a>
        </div>
    </body>
    </html>
    """

# =========================
# DESCARGAR ARCHIVOS
# =========================

@app.route("/downloads/<carpeta>/<archivo>")
def downloads(carpeta, archivo):
    return send_from_directory(f"outputs/{carpeta}", archivo, as_attachment=True)

# =========================
# EJECUTAR
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)