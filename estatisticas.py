import streamlit as st
import pandas as pd


def menu_estatisticas(clientes, fornecedores, produtos, vendas):
    st.header("📊 Menu Resumo Estatístico")

    menu_opcao = st.selectbox("Escolha uma opção:", [
        "Estatísticas Clientes",
        "Estatísticas Fornecedores",
        "Estatísticas Produtos",
        "Estatísticas Vendas",
        "Análises Complementares"
    ])

    if menu_opcao == "Estatísticas Clientes":
        st.subheader("Estatísticas Clientes")
        st.write(f"**Total de clientes:** {len(clientes)}")

    elif menu_opcao == "Estatísticas Fornecedores":
        st.subheader("Estatísticas Fornecedores")
        st.write(f"**Total de fornecedores:** {len(fornecedores)}")
        st.write("**Categorias disponíveis:**", fornecedores['categoria'].unique())
        st.write("**Contagem por categoria:**")
        st.dataframe(fornecedores['categoria'].value_counts().rename("Total"))

    elif menu_opcao == "Estatísticas Produtos":
        st.subheader("Estatísticas Produtos")
        estatisticas_produtos = produtos.drop(columns=['fornecedor_id','stock']).describe().round(2)
        st.dataframe(estatisticas_produtos)
        st.write(f"**Produtos sem stock:** {(produtos['stock'] == 0).sum()}")

    elif menu_opcao == "Estatísticas Vendas":
        st.subheader("Estatísticas Vendas")
        vendas = vendas.copy()
        vendas['data_venda'] = pd.to_datetime(vendas['data_venda'])

        estatisticas_vendas = vendas.drop(columns=['produto_id', 'cliente_id', 'data_venda']).describe().round(2)
        st.dataframe(estatisticas_vendas)

        vendas['mes'] = vendas['data_venda'].dt.strftime('%B')
        vendas['ordem_mes'] = vendas['data_venda'].dt.month

        vendas_por_mes = vendas.groupby(['ordem_mes', 'mes']).agg(
            total_vendas=('data_venda', 'count'),
            quantidade_total=('quantidade', 'sum')
        ).reset_index().sort_values('ordem_mes')

        st.write("### Resumo de Vendas por Mês")
        st.dataframe(vendas_por_mes[['mes', 'total_vendas', 'quantidade_total']].set_index('mes'))

    elif menu_opcao == "Análises Complementares":
        st.subheader("🔍 Análises Complementares")
        analise_opcao = st.radio("Selecione uma análise:", [
            "Distribuição de preços dos produtos",
            "Correlação entre preço e stock (produtos)",
            "Top 5 dos produtos mais vendidos"
        ])

        if analise_opcao == "Distribuição de preços dos produtos":
            produtos = produtos.copy()
            bins = 5
            cortes = pd.cut(produtos['preco'], bins=bins)

            # Gerar rótulos legíveis
            intervalos = cortes.cat.categories
            labels_legiveis = [f"{round(interval.left, 2)} – {round(interval.right, 2)}" for interval in intervalos]
            produtos['gama_preco'] = pd.cut(produtos['preco'], bins=bins, labels=labels_legiveis)
            distribuicao = produtos.groupby('gama_preco', observed=True).size().rename("Nº de produtos")
            st.write("### Distribuição de Preços dos Produtos (em 5 classes)")
            st.dataframe(distribuicao.reset_index())

        elif analise_opcao == "Correlação entre preço e stock (produtos)":
            correlacao = produtos[['preco', 'stock']].corr().round(2)
            st.write("### Correlação entre Preço e Stock")
            st.dataframe(correlacao)

        elif analise_opcao == "Top 5 dos produtos mais vendidos":
            top_produtos = vendas['produto_id'].value_counts().head(5).reset_index()
            top_produtos.columns = ['produto_id','Nº de Vendas']
            st.write("### Top 5 Produtos Mais Vendidos")
            st.dataframe(top_produtos)
    
   