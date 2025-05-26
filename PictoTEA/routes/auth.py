
from flask import Blueprint, render_template, request, redirect, url_for, session
import hashlib
from json_manager import leer_json, guardar_json
from user import User
from json_manager import verificar_credenciales
from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash

auth_bp = Blueprint('auth', __name__)


auth_bp = Blueprint('auth', __name__)
USUARIOS_PATH = 'data/usuarios.json'


def hash_contraseña(contraseña):
    return hashlib.sha256(contraseña.encode()).hexdigest()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not email or not password:
        return render_template('login.html', error='Debes completar todos los campos.')

    usuarios = leer_json(USUARIOS_PATH)
    contraseña_hashed = hash_contraseña(password)

    for u in usuarios:
        if u.get("email") == email and u.get("contraseña") == contraseña_hashed:
            usuario = User(u.get("email"))  # Asegúrate que tu clase User usa el email como ID
            login_user(usuario)
            return redirect(url_for('index'))

    return render_template('login.html', error='Credenciales incorrectas')

@auth_bp.route('/quien_eres')
def quien_eres():
    if current_user.is_authenticated:
        return jsonify({"usuario": current_user.id})
    return jsonify({"usuario": None})

@auth_bp.route('/logout')
def logout():
    logout_user()
    return jsonify({"success": True})

    

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        contraseña = request.form.get('password', '').strip()

        if not nombre or not email or not contraseña:
            return render_template('register.html', error='Todos los campos son obligatorios')

        usuarios = leer_json(USUARIOS_PATH)
        email_existente = False
        for usuario in usuarios:
            if usuario.get("email") == email:
                email_existente = True

        if email_existente:
            return render_template('register.html', error='Ya existe un usuario con ese email')

        nuevo_usuario = {
            "nombre": nombre,
            "email": email,
            "contraseña": hash_contraseña(contraseña)
        }

        usuarios.append(nuevo_usuario)
        guardar_json(USUARIOS_PATH, usuarios)

        return redirect(url_for('auth.login'))

    return render_template('register.html')
