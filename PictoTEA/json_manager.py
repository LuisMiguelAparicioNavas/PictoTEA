import json
import os

# Rutas absolutas relativas al proyecto
RUTA_USUARIOS = os.path.join(os.path.dirname(__file__), 'data', 'usuarios.json')
RUTA_FRASES = os.path.join(os.path.dirname(__file__), 'data', 'frases.json')


def cargar_json(ruta):
    """
    Carga el contenido de un archivo JSON. Si no existe, devuelve un diccionario vacío.
    """
    if not os.path.exists(ruta):
        return {}
    
    with open(ruta, 'r', encoding='utf-8') as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            return {}


import json
from pathlib import Path

def leer_json(ruta: str) -> list:
    """Lee un JSON y devuelve la lista de objetos."""
    path = Path(ruta)
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(ruta: str, datos: list) -> None:
    """Sobrescribe el JSON con la lista de objetos."""
    path = Path(ruta)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)



def registrar_usuario(nombre, email, contraseña):
    """
    Registra un nuevo usuario si no existe ni el nombre ni el email.
    Devuelve True si se registra correctamente, False si ya está registrado.
    """
    usuarios = cargar_json(RUTA_USUARIOS)

    # Comprobación por nombre y por email duplicado
    usuario_existe = False
    email_existe = False

    for nombre_existente in usuarios:
        if nombre_existente == nombre:
            usuario_existe = True
        if usuarios[nombre_existente].get("email") == email:
            email_existe = True

    if not usuario_existe and not email_existe:
        usuarios[nombre] = {
            "email": email,
            "password": contraseña
        }
        guardar_json(RUTA_USUARIOS, usuarios)
        return True

    return False


def verificar_credenciales(identificador, contraseña):
    """
    Verifica si el usuario existe con el nombre o email y que la contraseña sea correcta.
    """
    usuarios = cargar_json(RUTA_USUARIOS)

    for nombre_usuario, datos in usuarios.items():
        if identificador == nombre_usuario or identificador == datos.get("email"):
            if datos.get("password") == contraseña:
                return nombre_usuario  # Devuelve el nombre del usuario si todo es correcto

    return None



def guardar_frase(usuario, frase):
    """
    Guarda una frase para un usuario.
    """
    frases = cargar_json(RUTA_FRASES)

    if usuario not in frases:
        frases[usuario] = []

    frases_usuario = frases[usuario]

    if frase not in frases_usuario:
        frases_usuario.append(frase)

    frases[usuario] = frases_usuario
    guardar_json(RUTA_FRASES, frases)


def obtener_frases(usuario):
    """
    Devuelve las frases guardadas por un usuario.
    """
    frases = cargar_json(RUTA_FRASES)

    if usuario in frases:
        return frases[usuario]
    
    return []
