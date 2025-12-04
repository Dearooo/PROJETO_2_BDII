from modules.Conexao import get_database, test_connection
import base64
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.Conexao import run_query
from bson import ObjectId

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


image_logo = get_base64_image("assets/Logo.png")
image_usuario = get_base64_image("assets/Usuario.png")


containerHeader = st.container(horizontal= True, horizontal_alignment="left",gap="small")

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


containerBody = st.container(border=True)


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
    
        df_restaurantes = run_query(
            collection_name="restaurante",
            projection={"endereco.id": 1, "nomeFantasia": 1}
        )

        df_restaurantes = df_restaurantes.rename(columns={"nomeFantasia": "nome_fantasia", "endereco.id": "id_restaurante"})

        opcoes = [{"id_restaurante": 0, "nome_fantasia": "Todos"}] + [
            {"id_restaurante": str(r["_id"]), "nome_fantasia": r["nome_fantasia"]}
            for r in df_restaurantes.to_dict("records")
        ]


        restaurante_selecionado = st.selectbox(
            "Selecione o Restaurante",
            options=opcoes,
            format_func=lambda x: x["nome_fantasia"]
        )
        restaurante_selecionadoQuery = restaurante_selecionado["id_restaurante"]


        def MontarQueryCupom(data_inicio, data_fim, restaurante_selecionadoQuery):
            pipeline = [
                {
                    "$match": {
                        "data": {
                            "$gte": datetime.datetime.combine(data_inicio, datetime.time.min),
                            "$lte": datetime.datetime.combine(data_fim, datetime.time.max)
                        }
                    }
                },
                {"$unwind": "$itemCompras"},
                {
                    "$lookup": {
                        "from": "produto",
                        "localField": "itemCompras.produto.nome",
                        "foreignField": "nome",
                        "as": "produto_info"
                    }
                },
                {"$unwind": "$produto_info"},
            ]

    
            if restaurante_selecionadoQuery != 0:
                pipeline.append({
                    "$match": {"produto_info.restauranteId": ObjectId(restaurante_selecionadoQuery)}
                })

            pipeline.extend([
                {
                    "$group": {
                        "_id": "$cupom.porcentagemDesconto",
                        "total_cupons_usados": {"$sum": 1}
                    }
                },
                {"$sort": {"total_cupons_usados": -1}}
            ])

            df = run_query("pedido", aggregate_pipeline=pipeline)

            if "_id" in df.columns:
                df = df.rename(columns={"_id": "porcentagem_desconto"})

            if "porcentagem_desconto" in df.columns:
                df["porcentagem_desconto"] = df["porcentagem_desconto"].astype(str) + "%"
            else:
                df["porcentagem_desconto"] = []

            if "total_cupons_usados" not in df.columns:
                df["total_cupons_usados"] = []

            return df

    df1 = MontarQueryCupom(data_inicio, data_fim, restaurante_selecionadoQuery)
    fig1 = px.bar(
        df1,
        x="porcentagem_desconto",
        y="total_cupons_usados",
        title="Uso de Cupons por Restaurante",
        text="total_cupons_usados",
        color_discrete_sequence=["#FFCC80"]
        )

    fig1.update_traces(
        textposition='outside',
        marker_color="#FFCC80",
        width=0.4
    )
    fig1.update_layout(
        xaxis_title="Porcentagem de Desconto",
        yaxis_title="Total de Cupons Usados",
        title_x=0.5,
        xaxis=dict(type='category')
    )

    st.plotly_chart(fig1, use_container_width=True)
    st.write(df1)


with tab2:
    res = pd.DataFrame({"nome_restaurante": ["Todos"], "id": [0]})

    df_restaurantes = run_query(
        collection_name="restaurante",
        query={},
        projection={"_id": 1, "nomeFantasia": 1, "razaoSocial": 1}
    )

    df_restaurantes["nome_restaurante"] = df_restaurantes.apply(
        lambda r: f"{r['nomeFantasia']} ({r['razaoSocial']})", axis=1
    )
    df_restaurantes["id"] = df_restaurantes["_id"].astype(str)

    res = pd.concat([res, df_restaurantes[["nome_restaurante", "id"]]])
    option = st.selectbox("Selecione um restaurante", res['nome_restaurante'], index=0)
    restaurante_id = 0 if option is None else res.loc[res['nome_restaurante'] == option]['id'].values[0]

    pipeline = [
        {"$unwind": "$itemCompras"},
        {
            "$lookup": {
                "from": "produto",
                "localField": "itemCompras.produto.nome",
                "foreignField": "nome",
                "as": "produto_info"
            }
        },
        {"$unwind": "$produto_info"},
        {
            "$project": {
                "dia": {"$dateToString": {"format": "%Y-%m-%d", "date": "$data"}},
                "valor_item": {
                    "$multiply": [
                        "$itemCompras.qtde",
                        {"$toDouble": "$produto_info.preco"},
                        {
                            "$subtract": [
                                1,
                                {"$divide": ["$cupom.porcentagemDesconto", 100]}
                            ]
                        }
                    ]
                },
                "restaurante_id": "$produto_info.restauranteId"
            }
        }
    ]


    if restaurante_id != 0:
        pipeline.append({"$match": {"restaurante_id": ObjectId(restaurante_id)}})

    pipeline.extend([
        {
            "$group": {
                "_id": "$dia",
                "vendas": {"$sum": "$valor_item"}
            }
        },
        {"$sort": {"_id": 1}}
    ])
    vendas = run_query("pedido", aggregate_pipeline=pipeline)
    vendas = vendas.rename(columns={"_id": "dia"})

    if len(vendas) > 0:
        st.bar_chart(vendas, x='dia', y='vendas', x_label="Dia", y_label="Vendas", color='#FFCC80')
        st.write(vendas)
    else:
        st.write("Nenhum dado encontrado.")


with tab3:
    st.subheader("Métrica por Restaurante — Ticket Médio ou Cupons Usados")

    df_restaurantes = run_query(
        collection_name="restaurante",
        query={},
        projection={"_id": 1, "nomeFantasia": 1}
    )

    opcoes = [{"id_restaurante": "0", "nome_fantasia": "Todos"}] + [
        {"id_restaurante": str(r["_id"]), "nome_fantasia": r["nomeFantasia"]}
        for r in df_restaurantes.to_dict("records")
    ]

    restaurante_sel = st.selectbox(
        "Selecione o Restaurante",
        options=opcoes,
        format_func=lambda x: x["nome_fantasia"],
        key="graf3_multi"
    )
    restaurante_id = restaurante_sel["id_restaurante"]

    pipeline = [
        {"$unwind": "$itemCompras"},
        {
            "$lookup": {
                "from": "produto",
                "localField": "itemCompras.produto.nome",
                "foreignField": "nome",
                "as": "produto_info"
            }
        },
        {"$unwind": "$produto_info"},
        {
            "$lookup": {
                "from": "restaurante",
                "localField": "produto_info.restauranteId",
                "foreignField": "_id",
                "as": "restaurante_info"
            }
        },
        {"$unwind": "$restaurante_info"},
    ]

    if restaurante_id and restaurante_id != "0":
        try:
            pipeline.append({"$match": {"restaurante_info._id": ObjectId(restaurante_id)}})
        except Exception:
            st.warning("ID de restaurante inválido. Exibindo todos.")
            

    pipeline.extend([
        {
            "$project": {
                "restaurante": "$restaurante_info.nomeFantasia",
                "pedido_id": "$_id",
                "valor_item": {
                    "$multiply": [
                        "$itemCompras.qtde",
                        {"$toDouble": "$produto_info.preco"},
                        {
                            "$subtract": [
                                1,
                                {"$divide": ["$cupom.porcentagemDesconto", 100]}
                            ]
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$restaurante",
                "faturamento_total": {"$sum": "$valor_item"},
                "total_pedidos": {"$addToSet": "$pedido_id"}
            }
        },
        {
            "$project": {
                "restaurante": "$_id",
                "faturamento_total": 1,
                "total_pedidos": {"$size": "$total_pedidos"},
                "ticket_medio": {
                    "$cond": [
                        {"$gt": [{"$size": "$total_pedidos"}, 0]},
                        {"$round": [
                            {"$divide": ["$faturamento_total", {"$size": "$total_pedidos"}]},
                            2
                        ]},
                        0
                    ]
                }
            }
        },
        {"$sort": {"ticket_medio": -1}}
    ])


    df_ticket = run_query("pedido", aggregate_pipeline=pipeline)

    if df_ticket is None or df_ticket.empty:
        st.write("Nenhum dado encontrado para Ticket Médio.")
    else:
        fig = px.funnel(
            df_ticket,
            x="ticket_medio",
            y="restaurante",
            title="Ticket Médio por Restaurante (Funil)",
            color_discrete_sequence=["#FFCC80"],
        )
        fig.update_layout(
            title_x=0.5,
            xaxis_title="Ticket Médio (R$)",
            yaxis_title="Restaurante",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.write(df_ticket)





