from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import whisper
import ffmpeg
import io
import soundfile as sf
import funcionesPictogramas as fp
from flask import Flask
from routes.auth import auth_bp
from routes.frases import frases_bp
from flask_login import LoginManager
from user import User
from json_manager import cargar_json, RUTA_USUARIOS


app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_super_secreta_y_segura'
app.register_blueprint(auth_bp)
app.register_blueprint(frases_bp)

CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # el nombre del endpoint (ajusta si tu ruta se llama distinto)



@login_manager.user_loader
def load_user(user_id):
    from user import User
    return User.get_by_email(user_id)


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


@app.route('/')
def index():
    # Renderiza templates/index.html
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
