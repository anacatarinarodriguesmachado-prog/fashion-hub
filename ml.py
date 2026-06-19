import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

# Previsão de receita futura 
def prever_receita(vendas, produtos):
    # Garantir produto_id
    if "produto_id" not in produtos.columns:
        produtos = produtos.reset_index().rename(columns={"index": "produto_id"})

    # Juntar o preço ao DataFrame de vendas
    vendas = vendas.merge(produtos[["produto_id", "preco"]], on="produto_id", how="left")
    # Calcular a receita por venda
    vendas["receita"] = vendas["quantidade"] * vendas["preco"]

    # Converter datas e agrupar por mês
    vendas["data_venda"] = pd.to_datetime(vendas["data_venda"])
    vendas["ano_mes"] = vendas["data_venda"].dt.to_period("M").astype(str)

    # Obter receita total por mês
    receita_mensal = vendas.groupby("ano_mes")["receita"].sum().reset_index()

    # Preparar os dados para o modelo de previsão
    # X é o tempo (mês), e y é a receita.
    receita_mensal["indice"] = range(len(receita_mensal))
    X = receita_mensal[["indice"]]
    y = receita_mensal["receita"]

    # Treinar um modelo de regressão linear
    modelo = LinearRegression()
    modelo.fit(X, y)

    # Prever receita para os próximos 3 meses
    futuro = pd.DataFrame({"indice": [len(receita_mensal) + i for i in range(3)]})
    previsao = modelo.predict(futuro)

    return receita_mensal, previsao

# Clustering produtos
def clustering_produtos(produtos, vendas):

    # Juntar os preços aos dados de vendas
    vendas = vendas.merge(produtos[["produto_id", "preco"]], on="produto_id", how="left")
    # Calcular a receita
    vendas["receita"] = vendas["quantidade"] * vendas["preco"]

    resumo = vendas.groupby("produto_id").agg(
        total_receita=("receita", "sum"),
        total_quantidade=("quantidade", "sum")
    ).reset_index()

    # Preparar os dados para clustering
    resumo = resumo.merge(produtos[["produto_id", "nome"]], on="produto_id", how="left")

    # Aplicar K-Means para formar grupos
    X = resumo[["total_receita", "total_quantidade"]]
    modelo = KMeans(n_clusters=3, random_state=42, n_init=10)
    resumo["cluster"] = modelo.fit_predict(X)

    return resumo