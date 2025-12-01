import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Lê variáveis de ambiente
USERNAME = os.getenv("MONGO_USERNAME")
PASSWORD = os.getenv("MONGO_PASSWORD")
CLUSTER = os.getenv("MONGO_CLUSTER")
APP_NAME = os.getenv("MONGO_APP_NAME")
DB_NAME = os.getenv("MONGO_DB_NAME")

# Monta string de conexão
URI = f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/?appName={APP_NAME}"

def get_client():
    """
    Retorna o cliente MongoDB conectado
    """
    client = MongoClient(URI, server_api=ServerApi("1"))
    return client

def get_database():
    """
    Retorna o banco configurado no .env
    """
    client = get_client()
    return client[DB_NAME]

def test_connection():
    """
    Testa conexão usando ping
    """
    try:
        client = get_client()
        client.admin.command('ping')
        print("✅ MongoDB conectado com sucesso!")
    except Exception as e:
        print("❌ Erro na conexão MongoDB:")
        print(e)
