import mysql.connector
import streamlit as st
import seaborn as sns
import pandas as pd 
import datetime 
import plotly.express as px

from estatisticas import menu_estatisticas
from graficos import (
    grafico_vendas_por_mes,
    top_10_produtos_mais_vendidos,
    distribuicao_produtos_gama_preco,
    correlacao_preco_stock,
    distribuicao_fornecedores_categoria,
    boxplot_preco_categoria_fornecedor,
    mapa_calor_correlacoes)
from ml import prever_receita, clustering_produtos


def importar_dados_bd(query):
    conn = mysql.connector.connect(user='root', password='catarina', host='localhost', database='loja1', autocommit = True)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    st.title("👚 Welcome to Fashion Hub 👚")
    
    # Carregar dados da BD para visualizar os dados em tempo real 
    clientes = importar_dados_bd("SELECT * FROM clientes")
    fornecedores = importar_dados_bd("SELECT * FROM fornecedores")
    produtos = importar_dados_bd("SELECT * FROM produtos")
    vendas = importar_dados_bd("SELECT * FROM vendas")

    # Menu lateral para escolher entre visualização gráfica, estatísticas e previsões 
    st.sidebar.title("Menu de Navegação")
    menu_principal = st.sidebar.selectbox("Escolhe uma secção:", ["Resumo Estatístico", "Visualização Gráfica", "Machine Learning"])

    if menu_principal == "Visualização Gráfica":
        st.header("Menu de Visualização Gráfica")

        opcao = st.radio("Escolha a opção que pretende visualizar:", [
            "Vendas por Mês (Quantidade Total)",
            "Top 10 Produtos Mais Vendidos",
            "Distribuição de Produtos por Gama de Preço",
            "Correlação entre Preço e Stock dos Produtos",
            "Distribuição de Fornecedores por Categoria",
            "Boxplot de Preço por Categoria de Fornecedor",
            "Mapa de Calor das Correlações"
        ])

        if opcao == "Vendas por Mês (Quantidade Total)":
            st.pyplot(grafico_vendas_por_mes(vendas))

        elif opcao == "Top 10 Produtos Mais Vendidos":
            st.pyplot(top_10_produtos_mais_vendidos(vendas, produtos))

        elif opcao == "Distribuição de Produtos por Gama de Preço":
            st.pyplot(distribuicao_produtos_gama_preco(produtos))

        elif opcao == "Correlação entre Preço e Stock dos Produtos":
            st.pyplot(correlacao_preco_stock(produtos))

        elif opcao == "Distribuição de Fornecedores por Categoria":
            st.pyplot(distribuicao_fornecedores_categoria(fornecedores))

        elif opcao == "Boxplot de Preço por Categoria de Fornecedor":
            st.pyplot(boxplot_preco_categoria_fornecedor(produtos, fornecedores))

        elif opcao == "Mapa de Calor das Correlações":
            st.pyplot(mapa_calor_correlacoes(produtos))

    elif menu_principal == "Resumo Estatístico":
        menu_estatisticas(clientes, fornecedores, produtos, vendas)

    elif menu_principal == "Machine Learning":
        st.header("Machine Learning")

        submenu = st.radio("Seleciona uma análise:", ["Previsão de Receita Futura", "Clustering de Produtos"])

        # Previsão de Receita
        if submenu == "Previsão de Receita Futura":
            st.subheader("Previsão da receita futura")

            receita_mensal, previsao = prever_receita(vendas, produtos)

            st.subheader("Receita mensal (histórico)")
            st.line_chart(receita_mensal.set_index("ano_mes")["receita"])

            st.subheader("Previsão da receita para os próximos 3 meses:")

            # Calcular datas futuras com base na última
            ultima_data = pd.to_datetime(receita_mensal["ano_mes"].iloc[-1] + "-01")
            for i, valor in enumerate(previsao, start=1):
                proxima_data = ultima_data + pd.DateOffset(months=i)
                nome_mes = proxima_data.strftime("%B %Y")  # Ex: "Agosto 2025"
                st.write(f"{nome_mes}: **{valor:.2f} €**")

        # Clustering
        elif submenu == "Clustering de Produtos":
            # Obter os clusters
            clusters = clustering_produtos(produtos, vendas)
            clusters["preco_medio"] = clusters["total_receita"] / clusters["total_quantidade"]

            # Gráfico de dispersão com plotly 
            import plotly.express as px
            st.subheader("Visualização dos Clusters (Receita vs Quantidade Vendida)")
            fig = px.scatter(
                clusters,
                x="total_quantidade",
                y="total_receita",
                color="cluster",
                hover_data=["nome", "produto_id","preco_medio"],
                labels={
                    "total_quantidade": "Quantidade Vendida Total",
                    "total_receita": "Receita Total (€)",
                    "cluster": "Cluster",
                    "preco_medio": "Preço Médio (€)"
                },
                title="Distribuição de Produtos por Cluster"
            )
            st.plotly_chart(fig)

            st.subheader("Interpretação dos Clusters")
            st.markdown("""
            🔷 **Cluster 0 – Azul claro: Produtos com desempenho médio**  

            🔷 **Cluster 1 – Azul intermédio: Produtos de baixo desempenho**  

            🔷 **Cluster 2 – Azul escuro: Produtos premium**
            """)

main() 