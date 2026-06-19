import pandas as pd
import numpy as np
import csv
import beaupy 
from beaupy import select
import mysql.connector
import os
import getpass
import subprocess

# Ficheiro LOG 
from log import GenerateLOG
ficheiro_LOG = "logs.txt"


# Função para limpar o ecrã do terminal
def CLEAR():
    os.system('cls')

# Login no sistema 
def carregar_utilizadores(caminho='utilizadores.csv'):
    utilizadores = []
    with open(caminho, newline='', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            utilizadores.append(linha)
    return utilizadores

# carregar_utilizadores()

def fazer_login(utilizadores):
    tentativas = 3
    while tentativas > 0:
        print("👚 Welcome to Fashion Hub 👚\n\n")
        print("SISTEMA DE LOGIN\n")
        username = input("Nome de utilizador: ").strip()

        # Verifica se o utilizador existe
        utilizador_encontrado = None
        for u in utilizadores:
            if u['username'] == username:
                utilizador_encontrado = u
                break

        if utilizador_encontrado is None:
            print("⚠️ Utilizador não existe.\n")
            GenerateLOG("logs.txt", f"Tentativa de login com utilizador inexistente: {username}")
            continue 

        # Utilizador existe — pede palavra-passe escondida
        password = getpass.getpass("Palavra-passe: ").strip()

        if utilizador_encontrado['password'] != password:
            print("⚠️ Palavra-passe incorreta.\n")
            GenerateLOG("logs.txt", f"Palavra-passe incorreta para o utilizador: {username}")
        else:
            print(f"\n✅ Bem-vindo(a), {utilizador_encontrado['nome']}! ({utilizador_encontrado['categoria']})\n")
            return utilizador_encontrado

        tentativas -= 1
        print(f"Tentativas restantes: {tentativas}\n")

    print("❌ Número máximo de tentativas excedido. A sair do sistema.")
    GenerateLOG("logs.txt", "Número máximo de tentativas de login excedido.")
    exit()

# Conexão à base de dados
conn = mysql.connector.connect(user='root', password='catarina', host='localhost', autocommit = True)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS loja1")
cursor.execute("USE loja1")
# Tabela de clientes
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    email VARCHAR(100),
    telefone VARCHAR(9)
)
""")

# Tabela de fornecedores
cursor.execute("""
CREATE TABLE IF NOT EXISTS fornecedores (
    id_fornecedor INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    contacto VARCHAR(9),
    categoria VARCHAR(50)
)
""")

# Tabela de produtos
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    produto_id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50),
    preco DOUBLE,
    stock INT,
    fornecedor_id INT,
    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id_fornecedor)
        ON DELETE SET NULL ON UPDATE CASCADE
)
""")

# Tabela de vendas
cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    venda_id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT,
    cliente_id INT,
    quantidade INT NOT NULL,
    data_venda DATETIME,
    FOREIGN KEY (produto_id) REFERENCES produtos(produto_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente)
        ON DELETE SET NULL ON UPDATE CASCADE
)
""")

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# LIMPEZA E TRATAMENTO DE DADOS (UFCD 10808)
# ---------------------------------------------------------------------------------------------------------------------------------------------------
def limpar_tratar_dados():
    # LEITURA DOS FICHEIROS CSV
    clientes = pd.read_csv("clientes.csv",encoding="utf-8")
    fornecedores = pd.read_csv("fornecedores.csv",encoding="utf-8")
    produtos = pd.read_csv("produtos.csv",encoding="utf-8")
    vendas = pd.read_csv("vendas.csv",encoding="utf-8")

    # ------------------- CLIENTES (nome, email, telefone) -------------------------------------
    # NOME 
    clientes = clientes[~clientes['nome'].isnull()]  # remover nomes nulos/vazios
    clientes = clientes[clientes['nome'].str.len() > 3]  # remover nomes muito curtos (incompletos/inválidos)

    # EMAIL 
    clientes = clientes[~clientes['email'].isnull()]    # Remover emails nulos
    clientes['email'] = clientes['email'].str.lower()   # Converter emails para minúsculas
    clientes['email'] = clientes['email'].str.replace(r'@{2,}', '@', regex=True)    # Remover @ duplicados
    clientes['email'] = clientes['email'].str.strip()   # Remover espaços em branco antes/depois do email (caso existam)

    # TELEFONE 
    clientes['telefone'] = clientes['telefone'].str.replace(r'[\s\-]', '', regex=True)  # Remover espaços e traços
    clientes['telefone'] = clientes['telefone'].str.replace(r'\D', '', regex=True)  # Remover todos os caracteres que não são dígitos
    clientes = clientes[clientes['telefone'].str.len() == 9]    # Remover registos com telefone inválido (menos de 9 dígitos)

    # Salvar como CSV limpo
    clientes.to_csv("clientes_limpos.csv", index=False)

    # ----------------- FORNECEDORES (nome, contacto, categoria) ------------------------------
    # NOME
    fornecedores = fornecedores[~fornecedores['nome'].isnull()]     # Remover linhas com nome nulo
    fornecedores = fornecedores[fornecedores['nome'].str.strip() != ''] # Remover linhas com nome vazio

    # TELEFONE
    fornecedores['contacto'] = fornecedores['contacto'].str.replace(r'[\s\-]', '', regex=True)  # Remover espaços e traços
    fornecedores['contacto'] = fornecedores['contacto'].str.replace(r'\D', '', regex=True)  # Remover quaisquer caracteres não numéricos
    fornecedores = fornecedores[fornecedores['contacto'].str.len() == 9]

    # CATEGORIA
    fornecedores['categoria'] = fornecedores['categoria'].astype(str)
    fornecedores['categoria'] = fornecedores['categoria'].str.strip()   # Remover espaços antes e depois
    fornecedores = fornecedores[fornecedores['categoria'] != '']        # Remover linhas com categoria vazia 
    fornecedores = fornecedores[fornecedores['categoria'].str.lower() != 'nan']  # Remover linhas com categoria nula

    # Salvar como CSV limpo
    fornecedores.to_csv("fornecedores_limpos.csv", index=False)

    # ------------------ PRODUTOS (nome, preço, stock, fornecedor_id) ------------------------
    # NOME 
    produtos = produtos[~produtos['nome'].isnull()] # remover nomes vazios
    produtos = produtos[produtos['nome'].str.len() > 2] # remover nomes curtos (inválidos/incompletos)

    # PREÇO 
    produtos['preco'] = produtos['preco'].astype(str).str.replace(',', '.') # substituir vírgula por ponto para decimal
    produtos = produtos[pd.to_numeric(produtos['preco'], errors='coerce').notnull()]  # só valores numéricos
    produtos['preco'] = produtos['preco'].astype(float) # pode ser um float
    produtos = produtos[produtos['preco'] >= 0] # garantir que é número positivo
    produtos['preco'] = produtos['preco'].fillna(0.0) # substituir NaN por 0.0

    # STOCK
    produtos = produtos[pd.to_numeric(produtos['stock'], errors='coerce').notnull()]
    produtos['stock'] = produtos['stock'].fillna(0).astype(int) # substituir NaN por 0
    produtos['stock'] = produtos['stock'].astype(int)
    produtos = produtos[produtos['stock'] >= 0] # garantir que é inteiro positivo >= 0

    # FORNECEDOR_ID
    produtos = produtos[pd.to_numeric(produtos['fornecedor_id'], errors='coerce').notnull()]
    produtos['fornecedor_id'] = produtos['fornecedor_id'].astype(int)

    produtos = produtos.reset_index(drop=True) # redefinir os índices do DataFrame após as operações de limpeza
    produtos.to_csv("produtos_limpos.csv", index=False)

    # ------------------ VENDAS (produto_id, cliente_id, quantidade, data)--------------------
    from datetime import datetime
    # QUANTIDADE
    vendas['quantidade'] = pd.to_numeric(vendas['quantidade'], errors='coerce') # converter quantidade para valor numérico
    vendas = vendas[(vendas['quantidade'].notnull()) & (vendas['quantidade'] > 0)] # remover linhas com quantidade nula ou <= 0
    vendas['quantidade'] = vendas['quantidade'].astype(int) # converter quantidade para valor inteiro

    # DATA
    def formatar_data(data):
        formatos = [
            "%Y-%m-%d",  # 2025-06-11
            "%Y/%m/%d",  # 2025/06/10
            "%d-%m-%Y",  # 13-06-2025
            "%d/%m/%Y",  # 20/06/2025
            "%m-%d-%Y",  # 07-04-2025
            "%m/%d/%Y",  # 07/08/2025
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(data, fmt).date()
            except:
                continue
        return pd.NaT

    vendas['data_venda'] = vendas['data_venda'].astype(str).apply(formatar_data) # aplicar a função para converter a coluna data para datetime.date
    vendas = vendas[vendas['data_venda'].notnull()]   # remover linhas onde data é inválida 

    vendas = vendas.reset_index(drop=True)  # redefinir os índices 

    # Salvar como CSV limpo
    vendas.to_csv("vendas_limpo.csv", index=False)

# Para executar a função:
# limpar_tratar_dados()

# ********************************************************
# INSERÇÃO DOS DADOS DOS FICHEIROS CSV NA BASE DE DADOS
# ********************************************************

# idx - armazenar o índice da linha
# row - armazenar os dados da linha 
# iterrows - fazer operações linha a linha: inserir os dados na linha na BD

# Carregar os CSVs limpos
clientes = pd.read_csv("clientes_limpos.csv")
fornecedores = pd.read_csv("fornecedores_limpos.csv")
produtos = pd.read_csv("produtos_limpos.csv")
vendas = pd.read_csv("vendas_limpo.csv")

def inserir_dados_bd(clientes, fornecedores, produtos, vendas):
    # Conexão à base de dados
    conn = mysql.connector.connect(user='root', password='catarina', host='localhost', database='loja1', autocommit = True)
    cursor = conn.cursor()

    # Inserção CLIENTES
    for idx, row in clientes.iterrows(): 
        cursor.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s)",
            (row['nome'], row['email'], row['telefone'])
        )

    # Inserção FORNECEDORES
    for idx, row in fornecedores.iterrows():
        cursor.execute(
            "INSERT INTO fornecedores (nome, contacto, categoria) VALUES (%s, %s, %s)",
            (row['nome'], row['contacto'], row['categoria'])
        )

    # Inserção PRODUTOS
    for idx, row in produtos.iterrows():
        cursor.execute(
            "INSERT INTO produtos (nome, preco, stock, fornecedor_id) VALUES (%s, %s, %s, %s)",
            (row['nome'], row['preco'], row['stock'], row['fornecedor_id'])
        )

    # Inserção VENDAS
    for idx, row in vendas.iterrows():
        cursor.execute(
            "INSERT INTO vendas (produto_id, cliente_id, quantidade, data_venda) VALUES (%s, %s, %s, %s)",
            (row['produto_id'], row['cliente_id'], row['quantidade'], row['data_venda'])
        )

    # Confirmar as mudanças na base de dados
    conn.commit()

    print("Dados inseridos com sucesso!")

    cursor.close()
    conn.close()

# Chamar a função para inserir os dados
# inserir_dados_bd(clientes,fornecedores,produtos,vendas)

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# GESTÃO DAS TABELAS (CRUD - Create Read Update Delete)
# ---------------------------------------------------------------------------------------------------------------------------------------------------

conn = mysql.connector.connect(user='root', password='catarina', host='localhost', database='loja1', autocommit = True)
cursor = conn.cursor()

# ======== CLIENTES ========
def listar_cliente():
    cursor.execute("SELECT id_cliente, nome, email, telefone FROM clientes")
    clientes = cursor.fetchall()
    print("\n📋 Lista de Clientes:")
    for cliente in clientes:
        print(f"[{cliente[0]}] {cliente[1]} | {cliente[2]} | {cliente[3]}")
    print()

def inserir_cliente():
    nome = input("Nome do cliente:")
    email = input("Email:")
    while True:
        telefone = input("Telefone (9 dígitos): ")
        if telefone.isdigit() and len(telefone) == 9:
            break
        else:
            print("❌ Número inválido. Introduza um número com exatamente 9 dígitos.")
            erro = ("Numero de telemovel invalido.")
            GenerateLOG("logs.txt", erro) # Regista o erro no ficheiro de logs
 

    cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s)",
                   (nome, email, telefone))
    print("✅ Cliente adicionado com sucesso.\n")

def atualizar_cliente():
    listar_cliente()
    try:
        id_cliente = int(input("ID do cliente a atualizar: "))
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()

        if cliente is None:
            print("❌ Cliente não encontrado.\n")
            erro1 = ("Cliente não encontrado.")
            GenerateLOG("logs.txt", erro1) # Regista o erro no ficheiro de logs
            return

        print(f"Cliente atual: {cliente[1]} | {cliente[2]} | {cliente[3]}")
        novo_nome = input("Novo nome (deixa vazio para manter): ") or cliente[1]
        novo_email = input("Novo email (deixa vazio para manter): ") or cliente[2]
        novo_telefone = input("Novo telefone (deixa vazio para manter): ")
        if novo_telefone == "":
            novo_telefone = cliente[3]
        else:
            while not (novo_telefone.isdigit() and len(novo_telefone) == 9):
                print("❌ Número inválido. Introduz um número com exatamente 9 dígitos.")
                erro2 = ("Número de telemóvel inválido.")
                GenerateLOG("logs.txt", erro2) # Regista o erro no ficheiro de logs
                novo_telefone = input("Novo telefone (deixa vazio para manter): ")
                if novo_telefone == "":
                    novo_telefone = cliente[3]
                    break

        cursor.execute("""
            UPDATE clientes 
            SET nome = %s, email = %s, telefone = %s 
            WHERE id_cliente = %s
        """, (novo_nome, novo_email, novo_telefone, id_cliente))
        print("✏️ Cliente atualizado com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")

def remover_cliente():
    listar_cliente()
    try:
        id_cliente = int(input("ID do cliente a remover: "))
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()

        if cliente is None:
            print("❌ Cliente não encontrado.\n")
            erro3 = ("Cliente não encontrado.")
            GenerateLOG("logs.txt", erro3) # Regista o erro no ficheiro de logs
            return

        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        print("🗑️ Cliente removido com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")

# ======== FORNECEDORES ========

def listar_fornecedor():
    cursor.execute("SELECT id_fornecedor, nome, contacto, categoria FROM fornecedores")
    fornecedor = cursor.fetchall()
    print("\n📋 Lista de Fornecedores:")
    for f in fornecedor:
        print(f"[{f[0]}] {f[1]} | {f[2]} | {f[3]}")
    print()

def inserir_fornecedor():
    nome = input("Nome do fornecedor: ")
    while True:
        contacto = input("Contacto (9 dígitos): ")
        if contacto.isdigit() and len(contacto) == 9:
            break
        else:
            print("❌ Contacto inválido. Introduz um número com exatamente 9 dígitos.")
            erro4 = ("Número de telemóvel inválido.")
            GenerateLOG("logs.txt", erro4) # Regista o erro no ficheiro de logs

    categoria = input("Categoria: ")

    cursor.execute("INSERT INTO fornecedores (nome, contacto, categoria) VALUES (%s, %s, %s)",
                   (nome, contacto, categoria))
    print("✅ Fornecedor adicionado com sucesso.\n")

def atualizar_fornecedor():
    listar_fornecedor()
    try:
        id_fornecedor = int(input("ID do fornecedor a atualizar: "))
        cursor.execute("SELECT * FROM fornecedores WHERE id_fornecedor = %s", (id_fornecedor,))
        fornecedor = cursor.fetchone()

        if fornecedor is None:
            print("❌ Fornecedor não encontrado.\n")
            erro5 = ("Fornecedor não encontrado.")
            GenerateLOG("logs.txt", erro5) # Regista o erro no ficheiro de logs
            return

        print(f"Fornecedor atual: {fornecedor[1]} | {fornecedor[2]} | {fornecedor[3]}")
        novo_nome = input("Novo nome (deixa vazio para manter): ") or fornecedor[1]
        novo_contacto = input("Novo contacto (deixa vazio para manter): ")
        if novo_contacto == "":
            novo_contacto = fornecedor[2]
        else:
            while not (novo_contacto.isdigit() and len(novo_contacto) == 9):
                print("❌ Contacto inválido. Introduz um número com exatamente 9 dígitos.")
                erro6 = ("Numero de telemovel invalido.")
                GenerateLOG("logs.txt", erro6) # Regista o erro no ficheiro de logs
                novo_contacto = input("Novo contacto (deixa vazio para manter): ")
                if novo_contacto == "":
                    novo_contacto = fornecedor[2]
                    break
        nova_categoria = input("Nova categoria (deixa vazio para manter): ") or fornecedor[3]

        cursor.execute("""
            UPDATE fornecedores
            SET nome = %s, contacto = %s, categoria = %s
            WHERE id_fornecedor = %s
        """, (novo_nome, novo_contacto, nova_categoria, id_fornecedor))
        print("✏️ Fornecedor atualizado com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")


def remover_fornecedor():
    listar_fornecedor()
    try:
        id_fornecedor = int(input("ID do fornecedor a remover: "))
        cursor.execute("SELECT * FROM fornecedores WHERE id_fornecedor = %s", (id_fornecedor,))
        fornecedor = cursor.fetchone()

        if fornecedor is None:
            print("❌ Fornecedor não encontrado.\n")
            erro7 = ("Fornecedor não encontrado.")
            GenerateLOG("logs.txt", erro7) # Regista o erro no ficheiro de logs
            return

        cursor.execute("DELETE FROM fornecedores WHERE id_fornecedor = %s", (id_fornecedor,))
        print("🗑️ Fornecedor removido com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")

# ======== PRODUTOS ========

def listar_produto():
    cursor.execute("""
        SELECT produto_id, nome, preco, stock, fornecedor_id 
        FROM produtos
    """)
    produto = cursor.fetchall()
    print("\n📋 Lista de Produtos:")
    for p in produto:
        print(f"[{p[0]}] {p[1]} | Preço: {p[2]:.2f} | Stock: {p[3]} | Fornecedor ID: {p[4]}")
    print()

def inserir_produto():
    listar_produto()
    nome = input("Nome do produto: ")
    try:
        preco = float(input("Preço: "))
        if preco <= 0:
            print("❌ O preço deve ser maior que 0.\n")
            erro8 = ("Preco invalido.")
            GenerateLOG("logs.txt", erro8) # Regista o erro no ficheiro de logs
            return

        stock = int(input("Stock: "))
        if stock <= 0:
            print("❌ O stock deve ser maior que 0.\n")
            erro9 = ("Stock invalido.")
            GenerateLOG("logs.txt", erro9) # Regista o erro no ficheiro de logs
            return
        
        fornecedor_id = int(input("ID do fornecedor: "))
        
    except ValueError:
        print("⚠️ Dados inválidos. Preço deve ser número decimal e stock/fornecedor ID inteiro.\n")
        return

    cursor.execute("SELECT * FROM fornecedores WHERE id_fornecedor = %s", (fornecedor_id,))
    if cursor.fetchone() is None:
        print("❌ Fornecedor não encontrado.\n")
        erro10 = ("Fornecedor não encontrado.")
        GenerateLOG("logs.txt", erro10) # Regista o erro no ficheiro de logs
        return

    cursor.execute("""
        INSERT INTO produtos (nome, preco, stock, fornecedor_id) 
        VALUES (%s, %s, %s, %s)
    """, (nome, preco, stock, fornecedor_id))
    print("✅ Produto adicionado com sucesso.\n")

def atualizar_produto():
    listar_produto()
    try:
        produto_id = int(input("ID do produto a atualizar: "))
        cursor.execute("SELECT * FROM produtos WHERE produto_id = %s", (produto_id,))
        produto = cursor.fetchone()

        if produto is None:
            print("❌ Produto não encontrado.\n")
            erro11 = ("Produto não encontrado.")
            GenerateLOG("logs.txt", erro11) # Regista o erro no ficheiro de logs
            return

        print(f"Produto atual: {produto[1]} | Preço: {produto[2]:.2f} | Stock: {produto[3]} | Fornecedor ID: {produto[4]}")

        # Inputs como string
        novo_nome = input("Novo nome (deixa vazio para manter): ") or produto[1]

        # Conversões
        try:
            preco_input = input("Novo preço (deixa vazio para manter): ")
            novo_preco = float(preco_input) if preco_input.strip() else float(produto[2])
            if novo_preco <= 0:
                print("❌ O preço deve ser maior que 0.\n")
                erro12 = ("Preco invalido.")
                GenerateLOG("logs.txt", erro12) # Regista o erro no ficheiro de logs
                return

            stock_input = input("Novo stock (deixa vazio para manter): ")
            novo_stock = int(stock_input) if stock_input.strip() else int(produto[3])
            if novo_stock <= 0:
                print("❌ O stock deve ser maior que 0.\n")
                erro13 = ("Stock invalido.")
                GenerateLOG("logs.txt", erro13) # Regista o erro no ficheiro de logs
                return
            
            fornecedor_input = input("Novo fornecedor ID (deixa vazio para manter): ")
            novo_fornecedor_id = int(fornecedor_input) if fornecedor_input.strip() else int(produto[4])
        except ValueError:
            print("⚠️ Preço deve ser decimal e stock/fornecedor ID inteiros.\n")
            return

        # Verificar fornecedor
        cursor.execute("SELECT * FROM fornecedores WHERE id_fornecedor = %s", (novo_fornecedor_id,))
        fornecedor = cursor.fetchone()
        if fornecedor is None:
            print("❌ Fornecedor não encontrado.\n")
            erro14 = ("Fornecedor não encontrado.")
            GenerateLOG("logs.txt", erro14) # Regista o erro no ficheiro de logs
            return

        # Atualização
        cursor.execute("""
            UPDATE produtos
            SET nome = %s, preco = %s, stock = %s, fornecedor_id = %s
            WHERE produto_id = %s
        """, (novo_nome, novo_preco, novo_stock, novo_fornecedor_id, produto_id))
        print("✏️ Produto atualizado com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")

def remover_produto():
    listar_produto()
    try:
        produto_id = int(input("ID do produto a remover: "))
        cursor.execute("SELECT * FROM produtos WHERE produto_id = %s", (produto_id,))
        produto = cursor.fetchone()

        if produto is None:
            print("❌ Produto não encontrado.\n")
            erro15 = ("Produto não encontrado.")
            GenerateLOG("logs.txt", erro15) # Regista o erro no ficheiro de logs
            return

        cursor.execute("DELETE FROM produtos WHERE produto_id = %s", (produto_id,))
        print("🗑️ Produto removido com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")

# ======== VENDAS ========
def listar_venda():
    cursor.execute("""
        SELECT venda_id, produto_id, cliente_id, quantidade, data_venda
        FROM vendas
    """)
    vendas = cursor.fetchall()
    print("\n📋 Lista de Vendas:")
    for v in vendas:
        print(f"[{v[0]}] Produto ID: {v[1]} | Cliente ID: {v[2]} | Quantidade: {v[3]} | Data: {v[4]}")
    print()

def inserir_venda():
    from datetime import datetime
    # Produtos disponíveis
    cursor.execute("SELECT produto_id, nome FROM produtos")
    produtos = cursor.fetchall()
    if not produtos:
        print("❌ Nenhum produto disponível.\n")
        return

    opcoes_produto = [f"{p[0]} - {p[1]}" for p in produtos]
    print("Selecione um produto:")
    escolha_produto = select(opcoes_produto)
    if escolha_produto is None:
        print("❌ Operação cancelada.\n")
        return
    produto_id = int(escolha_produto.split(" - ")[0])

    # Clientes disponíveis
    cursor.execute("SELECT id_cliente, nome FROM clientes")
    clientes = cursor.fetchall()
    if not clientes:
        print("❌ Nenhum cliente disponível.\n")
        return

    opcoes_cliente = [f"{c[0]} - {c[1]}" for c in clientes]
    print("Selecione um cliente:")
    escolha_cliente = select(opcoes_cliente)
    if escolha_cliente is None:
        print("❌ Operação cancelada.\n")
        return
    cliente_id = int(escolha_cliente.split(" - ")[0])

    # Quantidade
    try:
        quantidade = int(input("Quantidade: "))
        if quantidade < 0:
            print("❌ A quantidade não pode ser negativa.\n")
            erro21 = "Tentativa de inserir quantidade negativa."
            GenerateLOG("logs.txt", erro21)
            return
    except ValueError:
        print("⚠️ Quantidade inválida. Deve ser um número inteiro.\n")
        return

    # Data atual
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Inserir venda
    cursor.execute("""
        INSERT INTO vendas (produto_id, cliente_id, quantidade, data_venda)
        VALUES (%s, %s, %s, %s)
    """, (produto_id, cliente_id, quantidade, data_atual))
    print("✅ Venda adicionada com sucesso.\n")

def atualizar_venda():
    listar_venda()
    from datetime import datetime
    try:
        venda_id = int(input("ID da venda a atualizar: "))
    except ValueError:
        print("⚠️ ID da venda inválido. Deve ser um número inteiro.\n")
        return

    cursor.execute("SELECT * FROM vendas WHERE venda_id = %s", (venda_id,))
    venda = cursor.fetchone()

    if venda is None:
        print("❌ Venda não encontrada.\n")
        erro18 = "Venda não encontrada."
        GenerateLOG("logs.txt", erro18)
        return

    print(f"Venda atual: Produto ID {venda[1]} | Cliente ID {venda[2]} | Quantidade {venda[3]} | Data {venda[4]}")

    # Novo produto 
    cursor.execute("SELECT produto_id, nome FROM produtos")
    produtos = cursor.fetchall()
    if not produtos:
        print("❌ Nenhum produto disponível.\n")
        return

    opcoes_produto = [f"{p[0]} - {p[1]}" for p in produtos]
    opcoes_produto.insert(0, "[Manter produto atual]")

    print("Selecione um novo produto:")
    escolha_produto = select(opcoes_produto)
    if escolha_produto is None:
        print("❌ Operação cancelada.\n")
        return

    if escolha_produto == "[Manter produto atual]":
        novo_produto_id = venda[1]
    else:
        novo_produto_id = int(escolha_produto.split(" - ")[0])

    # Novo cliente 
    cursor.execute("SELECT id_cliente, nome FROM clientes")
    clientes = cursor.fetchall()
    if not clientes:
        print("❌ Nenhum cliente disponível.\n")
        return

    opcoes_cliente = [f"{c[0]} - {c[1]}" for c in clientes]
    opcoes_cliente.insert(0, "[Manter cliente atual]")

    print("Selecione um novo cliente:")
    escolha_cliente = select(opcoes_cliente)
    if escolha_cliente is None:
        print("❌ Operação cancelada.\n")
        return

    if escolha_cliente == "[Manter cliente atual]":
        novo_cliente_id = venda[2]
    else:
        novo_cliente_id = int(escolha_cliente.split(" - ")[0])

    # Nova quantidade 
    nova_quantidade_input = input("Nova quantidade (deixa vazio para manter): ")
    if nova_quantidade_input.strip() == "":
        nova_quantidade = venda[3]
    else:
        try:
            nova_quantidade = int(nova_quantidade_input)
            if nova_quantidade < 0:
                print("❌ A quantidade não pode ser negativa.\n")
                erro22 = "Tentativa de atualizar para quantidade negativa."
                GenerateLOG("logs.txt", erro22)
                return
        except ValueError:
            print("⚠️ Quantidade inválida. Deve ser um número inteiro.\n")
            return

    # Atualizar venda 
    nova_data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        UPDATE vendas
        SET produto_id = %s, cliente_id = %s, quantidade = %s, data_venda = %s
        WHERE venda_id = %s
    """, (novo_produto_id, novo_cliente_id, nova_quantidade, nova_data, venda_id))

    print("✏️ Venda atualizada com sucesso.\n")
    
    
def remover_venda():
    listar_venda()
    try:
        venda_id = int(input("ID da venda a remover: "))
        cursor.execute("SELECT * FROM vendas WHERE venda_id = %s", (venda_id,))
        venda = cursor.fetchone()

        if venda is None:
            print("❌ Venda não encontrada.\n")
            erro21 = ("Venda não encontrada.")
            GenerateLOG("logs.txt", erro21) # Regista o erro no ficheiro de logs
            return

        cursor.execute("DELETE FROM vendas WHERE venda_id = %s", (venda_id,))
        print("🗑️ Venda removida com sucesso.\n")

    except ValueError:
        print("⚠️ ID inválido. Insere um número.\n")


def menu_clientes():
    while True:
        op = beaupy.select([
            "Listar Clientes",
            "Inserir Cliente",
            "Atualizar Cliente",
            "Remover Cliente",
            "Voltar"
        ], cursor="👉", cursor_style="cyan", return_index=True)

        match op:
            case 0:
                CLEAR()
                listar_cliente()
            case 1:
                CLEAR()
                inserir_cliente()
            case 2:
                CLEAR()
                atualizar_cliente()
            case 3:
                CLEAR()
                remover_cliente()
            case 4:
                CLEAR()
                break
            

def menu_fornecedores():
    while True:
        op = beaupy.select([
            "Listar Fornecedores",
            "Inserir Fornecedor",
            "Atualizar Fornecedor",
            "Remover Fornecedor",
            "Voltar"
        ], cursor="👉", cursor_style="cyan", return_index=True)

        match op:
            case 0:
                CLEAR()
                listar_fornecedor()
            case 1:
                CLEAR()
                inserir_fornecedor()
            case 2:
                CLEAR()
                atualizar_fornecedor()
            case 3:
                CLEAR()
                remover_fornecedor()
            case 4:
                break

def menu_produtos():
    while True:
        op = beaupy.select([
            "Listar Produtos",
            "Inserir Produto",
            "Atualizar Produto",
            "Remover Produto",
            "Voltar"
        ], cursor="👉", cursor_style="cyan", return_index=True)

        match op:
            case 0:
                CLEAR()
                listar_produto()
            case 1:
                CLEAR()
                inserir_produto()
            case 2:
                CLEAR()
                atualizar_produto()
            case 3:
                CLEAR()
                remover_produto()
            case 4:
                CLEAR()
                break

def menu_vendas():
    while True:
        op = beaupy.select([
            "Listar Vendas",
            "Inserir Venda",
            "Atualizar Venda",
            "Remover Venda",
            "Voltar"
        ], cursor="👉", cursor_style="cyan", return_index=True)

        match op:
            case 0:
                CLEAR()
                listar_venda()
            case 1:
                CLEAR()
                inserir_venda()
            case 2:
                CLEAR()
                atualizar_venda()
            case 3:
                CLEAR()
                remover_venda()
            case 4:
                CLEAR()
                break
            
def menu_tabelas():
    while True:
        print("\n=== MENU GERAL ===")
        op = beaupy.select([
            "Clientes",
            "Fornecedores",
            "Produtos",
            "Vendas",
            "Sair"
        ], cursor="👉", cursor_style="green", return_index=True)

        match op:
            case 0:
                menu_clientes()
            case 1:
                menu_fornecedores()
            case 2:
                menu_produtos()
            case 3:
                menu_vendas()
            case 4:
                print("👋 A sair...")
                break

# Chamar o menu para executar a gestão de tabelas  
# menu_tabelas()

def main():
    CLEAR()
    utilizadores = carregar_utilizadores()
    utilizador = fazer_login(utilizadores)
    if utilizador['categoria'].lower() == 'funcionario':
        print("\n📋 Menu do Funcionário:")
        menu_tabelas()
    elif utilizador['categoria'].lower() == 'gerente':
        while True:
            print("\n📋 Menu do Gerente:")
            op = beaupy.select([
            "1. Aceder ao menu de Tabelas",
            "2. Aceder ao menu de Estatísticas/Visualização Gráfica e Machine Learning",
            "3. Sair"
        ], cursor='->', cursor_style='green', return_index=True) + 1

            match op:
                case 1:
                    menu_tabelas()
                case 2:
                    print("A abrir menu de Estatísticas, Visualização Gráfica e de Previsão (Machine Learning)...")
                    subprocess.run(["streamlit", "run", "projeto.py"])
                case 3: 
                    print("👋 A sair...")
                    break

main() 