from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

# Carga variables de entorno desde .env
load_dotenv()


# Configuración de algoritmo de hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Info desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


# Función para hashear la pwd
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Función para verificar pwd
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Función para crear token de acceso
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()


    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})


    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
