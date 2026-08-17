import bcrypt
import database

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(username, password):
    user = database.get_user_by_username(username)
    if user:
        if check_password(password, user['password_hash']):
            return {"id": user['id'], "username": user['username'], "role": user['role']}
    return None
