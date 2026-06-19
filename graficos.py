# graficos.py
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import pandas as pd

def grafico_vendas_por_mes(vendas):
    vendas = vendas.copy()
    vendas['data_venda'] = pd.to_datetime(vendas['data_venda'])
    vendas_por_mes = vendas.groupby(vendas['data_venda'].dt.month).agg({'quantidade':'sum'}).reset_index()
    vendas_por_mes = vendas_por_mes.sort_values('data_venda')

    fig, ax = plt.subplots(figsize=(8,5))
    sns.lineplot(data=vendas_por_mes, x='data_venda', y='quantidade', marker='o', ax=ax)
    ax.set_title('Quantidade Total Vendida por Mês')
    ax.set_xlabel('Mês')
    ax.set_ylabel('Quantidade Vendida')
    ax.set_xticks(vendas_por_mes['data_venda'])
    ax.set_xticklabels([calendar.month_name[x] for x in vendas_por_mes['data_venda']], rotation=45)
    ax.grid(True)
    return fig

def top_10_produtos_mais_vendidos(vendas, produtos):
    top_produtos = vendas['produto_id'].value_counts().head(10).reset_index()
    top_produtos.columns = ['produto_id', 'Nº de Vendas']
    top_produtos = top_produtos.merge(produtos[['nome']], left_on='produto_id', right_index=True)

    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(data=top_produtos, y='nome', x='Nº de Vendas', palette='viridis', ax=ax)
    ax.set_title('Top 10 Produtos Mais Vendidos')
    ax.set_xlabel('Número de Vendas')
    ax.set_ylabel('Produto')
    return fig

def distribuicao_produtos_gama_preco(produtos):
    produtos = produtos.copy()
    produtos['gama_preco'] = pd.cut(produtos['preco'], bins=5)
    distribuicao = produtos['gama_preco'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(x=distribuicao.index.astype(str), y=distribuicao.values, palette='magma', ax=ax)
    ax.set_title('Distribuição de Produtos por Gama de Preço')
    ax.set_xlabel('Gama de Preço')
    ax.set_ylabel('Número de Produtos')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    return fig

def correlacao_preco_stock(produtos):
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=produtos, x='preco', y='stock', alpha=0.7, ax=ax)
    ax.set_title('Correlação entre Preço e Stock dos Produtos')
    ax.set_xlabel('Preço')
    ax.set_ylabel('Stock')
    return fig

def distribuicao_fornecedores_categoria(fornecedores):
    contagem_categoria = fornecedores['categoria'].value_counts()
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(contagem_categoria.values, labels=contagem_categoria.index, autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribuição de Fornecedores por Categoria')
    ax.axis('equal')
    return fig

def boxplot_preco_categoria_fornecedor(produtos, fornecedores):
    # verifica se a coluna 'id' existe no DataFrame fornecedores
    # Se não existir, redefine o índice para garantir que é numérico e sequencial e
    # cria uma nova coluna id com valores crescentes (index + 1).
    if 'id' not in fornecedores.columns:
        fornecedores = fornecedores.reset_index(drop=True)
        fornecedores['id'] = fornecedores.index + 1

    produtos = produtos.copy()
    produtos['fornecedor_id'] = produtos['fornecedor_id'].astype(int)
    prod_fornec = produtos.merge(fornecedores[['id', 'categoria']], left_on='fornecedor_id', right_on='id', how='left')

    fig, ax = plt.subplots(figsize=(10,6))
    sns.boxplot(data=prod_fornec, x='categoria', y='preco', ax=ax)
    ax.set_title('Distribuição do Preço dos Produtos por Categoria de Fornecedor')
    ax.set_xlabel('Categoria')
    ax.set_ylabel('Preço')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    return fig

def mapa_calor_correlacoes(produtos):
    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(produtos.select_dtypes(include='number').corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
    ax.set_title('Mapa de Calor das Correlações (Produtos)')
    return fig