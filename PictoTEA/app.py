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

@app.route('/')
def index():
    sesionIniciada = False
    if "usr_id" in session:
        sesionIniciada = True
    return render_template('index.html', sesionIniciada=sesionIniciada)

@app.route("/register")
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/tus_frases')
def tus_frases():
    if 'usr_id' not in session:
        return redirect(url_for('login'))

    frases_total = []
    if os.path.exists("data/frases.json"):
        with open("data/frases.json", "r") as f:
            try:
                frases_total = json.load(f)
            except json.JSONDecodeError:
                frases_total = []

    frasesUSR = [d for d in frases_total if d.get("id") == session["usr_id"]]
    pictogramas = [frase.get("pictogramas", []) for frase in frasesUSR]

    return render_template('tusFrases.html', pictogramas=pictogramas)

@app.route('/libreriaPictos')
def libreriaPictos():
    sesionIniciada = False
    if "usr_id" in session:
        sesionIniciada = True
    return render_template('libreriaPictos.html', sesionIniciada=sesionIniciada)

@app.route('/añadir', methods=['POST'])
def añadir():
    if 'usr_id' not in session:
        return jsonify({"error": "no_session"}), 401

    usr_id = session['usr_id']
    frases_total = []

    # Leer archivo existente si hay
    if os.path.exists("data/frases.json"):
        with open("data/frases.json", "r") as f:
            try:
                frases_total = json.load(f)
            except json.JSONDecodeError:
                frases_total = []

    # Obtener datos enviados
    data = request.get_json()
    pictogramas = data.get("pictogramas", [])

    if not pictogramas or not isinstance(pictogramas, list):
        return jsonify({"error": "Datos inválidos"}), 400

    # Crear nueva entrada
    nueva_frase = {
        "id": usr_id,
        "pictogramas": pictogramas
    }

    frases_total.append(nueva_frase)

    # Guardar en archivo
    with open("data/frases.json", "w") as f:
        json.dump(frases_total, f, indent=2)

    return jsonify({"mensaje": "Frase añadida correctamente"}), 200

@app.route('/autenticar', methods=["POST"])
def autenticar():
    mail = request.form.get('email')
    password = str(request.form.get('password'))
    hashed_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()

    usuarios = []

    if os.path.exists("data/users.json"):
        with open("data/users.json", "r") as j:
            try:
                usuarios = json.load(j)
            except json.JSONDecodeError:
                usuarios = []
    
    usuario = next((d for d in usuarios if d.get("mail") == mail and d.get("pass") == hashed_pass), None)
    
    print (usuario)
    if usuario:
        session["usr_id"] = usuario["id"]
        if "usr_id" in session:
            print("Se ha guardado en la variable de sesion")
        return jsonify({"success": True, "message": "Login exitoso"}), 200
    else:
        return jsonify({"success": False, "message": "Contraseña o email incorrectos"}), 401

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

@app.route("/redirigir1")
def redirigir1():
    if 'usr_id' not in session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('tus_frases'))

@app.route("/registrarUsuario", methods=["POST"])
def registrarUsuario():
    nombre = request.form.get('nombre')
    mail = request.form.get('mail')
    contrasena = str(request.form.get('contrasena'))
    
    usuarios = []
    if os.path.exists("data/users.json"):
        with open("data/users.json", "r") as j:
            try:
                usuarios = json.load(j)
            except json.JSONDecodeError:
                usuarios = []

    hashed_pass = hashlib.sha256(contrasena.encode('utf-8')).hexdigest()
    datosUsuario = {"id": len(usuarios) + 1,"nombre": str(nombre), "mail": str(mail), "pass" : hashed_pass}
    usuarios.append(datosUsuario)

    with open("data/users.json", "w") as j:
        json.dump(usuarios, j, indent=2)

    return "Registro exitoso", 200

@app.route("/logout")
def logout():
    if "usr_id" in session:
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
