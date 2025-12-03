from modules.Conexao import get_database, test_connection
import base64
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.Conexao import run_query
# Testa conexão
test_connection()

# Acessa banco
db = get_database()

print("Banco de dados acessado com sucesso:", db.name)



#configuração inicial do site
st.set_page_config(
    page_title="Análise",
    page_icon="assets/Logo.png",
    layout="wide"
)


#Convertendo para base64 para o streamlit reconhecer.
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Caminho relativo da sua imagem
image_logo = get_base64_image("assets/Logo.png")
image_usuario = get_base64_image("assets/Usuario.png")

#criando o header
containerHeader = st.container(horizontal= True, horizontal_alignment="left",gap="small")
#cria o visual do header e estiliza
containerHeader.markdown(f"""
<style>
.header-container {{
    display: flex;
    align-items: center;
    border-bottom: 3px solid #ff9800;
    padding: 10px 0;
    justify-content: space-between;
}}
.header-logo {{
    width: 50px;
    margin-right: 15px;
}}
.header-text {{
    color: #ff9800;
    font-family: 'Segoe UI', sans-serif;
    font-size: 1.5rem;
    margin: 0;
    padding: 0;
}}
.ancora {{
    text-decoration: none !important;
    color: #ff9800 !important;
}}
.ancora:hover {{
    text-decoration: none !important;
    color: #ffa726 !important;
    font-size: 15px;
}}
.ancora img {{
    margin-left: 10px;
    width: 55px;
    border-radius: 50%;
}}
</style>

<div class="header-container">
    <div style="display: flex; align-items: center;">
        <img class="header-logo" src="data:image/png;base64,{image_logo}">
        <h4 class="header-text">Painel de Gerenciamento de Informações do Estabelecimento</h4>
    </div>
    <a href="#" class="ancora">
        Carlos - Diretor
        <img src="data:image/png;base64,{image_usuario}">
    </a>
</div>
""", unsafe_allow_html=True)

#criando o body.
containerBody = st.container(border=True)

#estilo da aba
st.markdown("""
<style>
.stTabs [role="tab"] {
    color: #ff9800;  /* cor do texto das abas inativas */
    background-color: #1e1e1e;  /* fundo padrão */
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
    font-weight: 500;
}

.stTabs [role="tab"][aria-selected="true"] {
    color: white !important;          /* fonte branca */
    background-color: #ff9800 !important; /* fundo laranja */
    font-weight: bold;
}

.stTabs [role="tab"]:hover {
    background-color: #ffb74d;
    color: white;
}
</style>
""", unsafe_allow_html=True)




#criando as abas que contem os relatórios.
tab1, tab2, tab3 = containerBody.tabs(["Grafico1", "Grafico2", "Grafico3"])

with tab1:
    hoje = datetime.date.today()
    data_grafico = hoje - datetime.timedelta(days=360)
    restaurante_selecionadoQuery = 0
    col1, col2, col3 = st.columns([0.1, 0.1, 0.8])
    with col1:
        data_inicio = st.date_input("Data inicial",format= "DD/MM/YYYY", value= data_grafico)
    with col2:
        data_fim = st.date_input("Data final", format= "DD/MM/YYYY", value = hoje)
    with col3:
        queryRestaurantes = """
        SELECT
            r.id AS id_restaurante,
            r.nome_fantasia AS nome_fantasia
            FROM restaurante r
        """
        df_restaurantes = run_query(queryRestaurantes)

        # Adiciona a opção "Todos" manualmente
        opcoes = [{"id_restaurante": 0, "nome_fantasia": "Todos"}] + df_restaurantes.to_dict("records")

        # Cria o selectbox mostrando nome, mas armazenando id
        restaurante_selecionado = st.selectbox(
            "Selecione o Restaurante",
            options=opcoes,
            format_func=lambda x: x["nome_fantasia"]
        )
        restaurante_selecionadoQuery = restaurante_selecionado["id_restaurante"]

    def MontarQueryCupom():
        queryCupom = """
            SELECT
                c.porcentagem_desconto AS porcentagem_desconto,
                COUNT(p.id) AS total_cupons_usados
            FROM pedido p
        """

        queryCupomJoin = """
            JOIN cupom c ON p.cupom_aplicado = c.id
        """

        queryRestaurantesJoin = """
            JOIN item_compra ic ON p.id = ic.id_pedido
            JOIN produto pd ON ic.id_produto = pd.id
            JOIN restaurante r ON pd.id_restaurante = r.id
        """

        queryCupomWhere = """
            WHERE p.data BETWEEN %s AND %s
        """

        queryRestaurantesWhere = """
            AND r.id = %s
        """

        queryGroup = """
            GROUP BY c.porcentagem_desconto
            ORDER BY total_cupons_usados DESC;
        """

        # Monta os parâmetros
        params = [data_inicio, data_fim]

        if restaurante_selecionadoQuery != 0:
            queryCupom = (
                queryCupom
                + queryCupomJoin
                + queryRestaurantesJoin
                + queryCupomWhere
                + queryRestaurantesWhere
                + queryGroup
            )
            params.append(restaurante_selecionadoQuery)
        else:
            queryCupom = queryCupom + queryCupomJoin + queryCupomWhere + queryGroup

        return queryCupom, tuple(params)
