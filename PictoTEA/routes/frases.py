from flask import Blueprint, render_template, request, redirect, url_for, session
import hashlib
from json_manager import leer_json, guardar_json
from flask import jsonify


auth_bp = Blueprint('auth', __name__)
USUARIOS_PATH = 'data/usuarios.json'

frases_bp = Blueprint('frases', __name__)
FRASES_PATH = 'data/frases.json'



def obtener_frases_usuario(email):
    frases_data = leer_json(FRASES_PATH)
    if not frases_data:
        return []

    for usuario in frases_data:
        if usuario.get("email") == email:
            return usuario.get("frases", [])
    return []

def guardar_frases_usuario(email, frases):
    frases_data = leer_json(FRASES_PATH) or []
    
    usuario_encontrado = False
    for usuario in frases_data:
        if usuario.get("email") == email:
            usuario["frases"] = frases
            usuario_encontrado = True

    if not usuario_encontrado:
        frases_data.append({
            "email": email,
            "frases": frases
        })

    guardar_json(FRASES_PATH, frases_data)

@frases_bp.route('/tusFrases')
def tus_frases():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    email = session['email']
    frases = obtener_frases_usuario(email)
    nombre = session.get('nombre', '')

    return render_template('tusFrases.html', frases=frases, nombre=nombre)

@frases_bp.route('/tusFrases/data')
def tus_frases_data():
    if 'email' not in session:
        return jsonify({"frases": []})  # No está autenticado

    email = session['email']
    frases = obtener_frases_usuario(email)
    return jsonify({"frases": frases})


@frases_bp.route('/agregarFrase', methods=['POST'])
def agregar_frase():
    if 'email' not in session:
        return jsonify({"error": "No autenticado"}), 401

    email = session['email']
    frase_nueva = request.form.get('frase', '').strip()

    if not frase_nueva:
        return jsonify({"error": "Frase vacía"}), 400

    frases = obtener_frases_usuario(email)
    frases.append(frase_nueva)
    guardar_frases_usuario(email, frases)

    # Para que no recargue o redirija, devolvemos JSON
    return jsonify({"mensaje": "Frase añadida correctamente", "frase": frase_nueva})

