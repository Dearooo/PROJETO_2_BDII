import streamlit as st
import pandas as pd
import psycopg2.pool
import os
from dotenv import load_dotenv

# Caminho absoluto para o .env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
print(f"🔍 Carregando .env de: {env_path}")

# Carrega o .env explicitamente
load_dotenv(dotenv_path=env_path)

# Debug: imprime as variáveis para conferir
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
print("DB_PORT:", os.getenv("DB_PORT"))

@st.cache_resource
def get_connection_pool():
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
    return connection_pool

def init_connection():
    try:
        conn = connection_pool.getconn()
        print("✅ Conexão bem-sucedida com:", os.getenv('DB_HOST'))
        return conn
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        print("❌ Erro detalhado:", e)
        return None

def close_connection(conn):
    try:
        connection_pool.putconn(conn)
        print("✅ Conexão retornada ao pool")
    except Exception as e:
        st.error(f"Erro ao retornar conexão ao pool: {e}")

#função para executar querys;
#@st.cache_data(ttl=3600) # Possivelmente causa problemas
def run_query(query, params = None):
    conn = init_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro na query: {e}")
        return pd.DataFrame()
    finally:
        close_connection(conn=conn)
        
connection_pool = get_connection_pool()