import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, render_template, redirect, url_for

app = Flask(__name__)

# Configuración por variables de entorno (sin autenticación de la app,
# solo credenciales de conexión a la BD)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "personasdb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")


def get_connection():
    """Crea una conexión a la base de datos, reintentando si todavía no está
    lista (típico al levantar contenedores/pods donde el orden de arranque
    no está garantizado)."""
    intentos = 10
    espera = 3
    ultimo_error = None
    for i in range(intentos):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                # Fuerza mensajes de error en formato simple (sin tildes/ñ)
                # para evitar crashes de decodificación en Windows con
                # locales no-UTF8 (issue conocido de psycopg2)
                options="-c lc_messages=C",
            )
            return conn
        except psycopg2.OperationalError as e:
            ultimo_error = e
            print(f"[DB] Intento {i + 1}/{intentos} fallido, reintentando en {espera}s...")
            time.sleep(espera)
    raise ultimo_error


def init_db():
    """Crea la tabla 'personas' si no existe todavía."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            documento INTEGER NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# API REST
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/personas", methods=["GET"])
def listar_personas():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nombre, apellido, documento FROM personas ORDER BY id;")
    personas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(personas)


@app.route("/api/personas/<int:persona_id>", methods=["GET"])
def obtener_persona(persona_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, nombre, apellido, documento FROM personas WHERE id = %s;",
        (persona_id,),
    )
    persona = cur.fetchone()
    cur.close()
    conn.close()
    if persona is None:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(persona)


@app.route("/api/personas", methods=["POST"])
def crear_persona():
    data = request.get_json(silent=True) or request.form
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    documento = data.get("documento")

    if not nombre or not apellido or not documento:
        return jsonify({"error": "Faltan campos: nombre, apellido, documento"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO personas (nombre, apellido, documento) VALUES (%s, %s, %s) RETURNING id;",
        (nombre, apellido, documento),
    )
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(
        {"id": nuevo_id, "nombre": nombre, "apellido": apellido, "documento": documento}
    ), 201


# ---------------------------------------------------------------------------
# Páginas web simples (1 de lectura, 1 de escritura)
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return redirect(url_for("pagina_leer"))


@app.route("/leer")
def pagina_leer():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nombre, apellido, documento FROM personas ORDER BY id;")
    personas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("leer.html", personas=personas)


@app.route("/escribir", methods=["GET", "POST"])
def pagina_escribir():
    mensaje = None
    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        documento = request.form.get("documento")

        if nombre and apellido and documento:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO personas (nombre, apellido, documento) VALUES (%s, %s, %s);",
                (nombre, apellido, documento),
            )
            conn.commit()
            cur.close()
            conn.close()
            mensaje = "Persona guardada correctamente."
        else:
            mensaje = "Error: completá todos los campos."

    return render_template("escribir.html", mensaje=mensaje)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)