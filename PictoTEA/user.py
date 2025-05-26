# user.py
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, email):
        self.id = email  # Flask-Login usa `.id` por defecto

    @staticmethod
    def get_by_email(email):
        from json_manager import leer_json
        usuarios = leer_json('data/usuarios.json')
        for u in usuarios:
            if u.get("email") == email:
                return User(email)
        return None
