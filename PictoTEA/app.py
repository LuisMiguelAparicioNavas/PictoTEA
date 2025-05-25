from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import whisper
import ffmpeg
import io
import soundfile as sf
import static.funcionesPictogramas as fp

app = Flask(__name__)  # por defecto, templates_folder="templates" y static_folder="static"
CORS(app)

# Carga el modelo Whisper solo una vez
model = whisper.load_model("base")


@app.route('/')
def index():
    # Renderiza templates/index.html
    return render_template('index.html')


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


if __name__ == '__main__':
    # Ejecuta en 0.0.0.0:5000
    app.run(host='0.0.0.0', port=5000, debug=True)
