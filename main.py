from modules.Conexao import get_database, test_connection

# Testa conexão
test_connection()

# Acessa banco
db = get_database()

print("Banco de dados acessado com sucesso:", db.name)

