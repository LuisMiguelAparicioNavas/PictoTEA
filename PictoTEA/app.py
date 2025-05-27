from flask import Flask, request, jsonify, render_template, request, redirect,url_for, session
from flask_cors import CORS
import whisper
import ffmpeg
import io
import soundfile as sf
import static.funcionesPictogramas as fp
import json
import hashlib
import os

app = Flask(__name__)  # por defecto, templates_folder="templates" y static_folder="static"
CORS(app)


categorias = [
    ["food", "beverage", "gastronomy", "taste", "cookery"], #Alimentacion
    ["sports", "games", "musical art", "show", "hobby", "outdoor activity", "entertainment facility", "toy"], #Ocio
    ["animal anatomy", "wild animal", "domestic animal", "marine animal", "flying animal", "terrestrial animal", "tree", "bush", "cactus", "fungus", "flower", "aromatic plant", "plant", "extinct being"], #Ser vivo
    ["monument", "building", "facility", "urban area", "infrastructure", "workplace", "rural area"], #Lugar
    ["event", "calendar", "unit of time", "chronological device"], #Tiempo
    ["traffic", "land transport","aerial transport", "water transport"], #Desplazamiento
    ["christianity", "judaism", "islam", "hinduism", "budism", "religious place", "religion"], #Religion
    ["work", "work organization", "professional"], #Trabajo
    ["communication system", "mass media", "tv show", "telecommunication"], #Comunicación
    ["furniture", "appliance", "clothes"], #Objetos
    ["art","science","literature"] #Conocimiento
]

# Carga el modelo Whisper solo una vez
model = whisper.load_model("base")

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'
USUARIOS_PATH = './data/users.json'

def leer_json(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def hash_contraseña(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def encontrar_usuario(email, password_hash):
    usuarios = leer_json(USUARIOS_PATH)
    usuario_valido = None
    # Buscamos sin return dentro del bucle
    for u in usuarios:
        if u.get("email") == email and u.get("contraseña") == password_hash:
            usuario_valido = u
    return usuario_valido

@app.route("/register")
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Mostramos el formulario de login
        return render_template('login.html')

    # Procesamos el POST
    email    = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # Validamos que no vengan vacíos
    if not email or not password:
        return render_template('login.html', error='Debes completar todos los campos.')

    # Hash de la contraseña y búsqueda de usuario
    password_hash = hash_contraseña(password)
    usuario_data  = encontrar_usuario(email, password_hash)

    if usuario_data:
        # Login OK: guardamos los datos en session
        session['usuario'] = {
            'email': usuario_data['email'],
            'nombre': usuario_data['nombre']
        }
        # Redirigimos al destino guardado (o al home por defecto)
        destino = session.pop('next', None)
        return redirect(destino or url_for('index'))

    # Si llegamos aquí, credenciales incorrectas
    return render_template('login.html', error='Credenciales incorrectas')


@app.route('/tus_frases')
def tus_frases():
    if 'usuario' not in session:
        session['next'] = url_for('tus_frases')
        return redirect(url_for('login'))
    return render_template('tusFrases.html')

@app.route('/añadir')
def añadir():
    if 'usuario' not in session:
        session['next'] = url_for('index')
        return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/libreriaPictos')
def libreriaPictos():
    return render_template('libreriaPictos.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    # 1) Lee el audio subido
    audio_bytes = request.files['audio'].read()

    # 2) Convierte WebM/Opus a WAV PCM16 mono 16 kHz en memoria
    process = (
        ffmpeg
        .input('pipe:0')
        .output('pipe:1',
                format='wav',
                acodec='pcm_s16le',
                ac=1,
                ar='16000')
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )
    wav_bytes, _ = process.communicate(audio_bytes)

    # 3) Cargo el WAV en un numpy array float32
    audio_np, sr = sf.read(io.BytesIO(wav_bytes), dtype='float32')

    # 4) Transcribo con Whisper
    result = model.transcribe(audio_np, language="es")

    # 5) Devuelvo JSON
    return jsonify({'texto': result['text']})

@app.route("/pictogramas", methods=['POST'])
def pictogramas():
    #Coger la frase del campo de texto
    frase = request.form.get('inputFrase')
    #Llamar a la función que pasa de frases a pictogramas
    resultados = fp.texto_a_pictogramas_arasaac(frase)
    #Devolver resultados tipo JSON
    return jsonify(resultados)


@app.route("/registrarUsuario", methods=["POST"])
def registrarUsuario():
    nombre = request.form.get('nombre')
    mail = request.form.get('mail')
    contrasena = str(request.form.get('contrasena'))
    
    hashed_pass = hashlib.sha256(contrasena.encode('utf-8')).hexdigest()
    datosUsuario = {"nombre": str(nombre), "mail": str(mail), "pass" : hashed_pass}

    usuarios = []
    if os.path.exists("data/users.json"):
        with open("data/users.json", "r") as j:
            try:
                usuarios = json.load(j)
            except json.JSONDecodeError:
                usuarios = []

    usuarios.append(datosUsuario)

    with open("data/users.json", "w") as j:
        json.dump(usuarios, j, indent=2)

    return "Registro exitoso", 200

@app.route("/logout")
def logout():
    if "usuario" in session:
        session.clear()
    return redirect(url_for('login'))

@app.route("/get_categoria", methods=['POST'])
def get_categoria():
    try:
        categoria_idx = int(request.form.get("categoria"))
        
        if 0 <= categoria_idx < len(categorias):
            categoria_keywords = categorias[categoria_idx]
            pictos_tuplas = fp.obtener_pictogramas_por_categoria(categoria_keywords)
            
            # Convertir las tuplas a diccionarios que espera el JavaScript
            if pictos_tuplas:
                pictos_dict = []
                for palabra, url in pictos_tuplas:
                    pictos_dict.append({
                        "palabra": palabra,
                        "url": url
                    })
                return jsonify({"pictos": pictos_dict})
            else:
                return jsonify({"pictos": []})
        
        return jsonify({"error": "Categoría inválida"}), 400
        
    except Exception as e:
        print(f"Error en get_categoria: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


if __name__ == '__main__':
    # Ejecuta en 0.0.0.0:5000
    app.run(host='0.0.0.0', port=5000, debug=True)
