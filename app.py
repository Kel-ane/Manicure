# ==========================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# ==========================================================
from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
import pandas as pd
import os
# ==========================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==========================================================

# Cria a aplicação Flask
app = Flask(__name__)

# ==========================================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================================


def conectar():
    """
    Realiza a conexão com o banco de dados MySQL.
    """

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="mydb"
    )
# ==========================================================
# CRIAÇÃO DAS TABELAS DO BANCO DE DADOS
# ==========================================================


def criar_tabelas():
    """
    Cria as tabelas do sistema caso ainda não existam.
    """
    conexao = conectar()
    cursor = conexao.cursor()

    # ------------------------------------------------------
    # Tabela de Clientes
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(50),
            telefone VARCHAR(20),
            cpf VARCHAR(14),
            data_nascimento DATE,
            bairro VARCHAR(50),
            rua VARCHAR(100),
            numero_casa VARCHAR(10),
            cidade VARCHAR(50),
            estado VARCHAR(2),
            cep VARCHAR(9),
            complemento VARCHAR(100)
        )
    """)

    # ------------------------------------------------------
    # Tabela de Serviços
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            valor DECIMAL(10,2)
        )
    """)

    # ------------------------------------------------------
    # Tabela de Agendamentos
    # ------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id_agendamento INT AUTO_INCREMENT PRIMARY KEY,
            id_cliente INT,
            id_servico INT,
            forma_pagamento VARCHAR(30),
            data_hora DATETIME,

            FOREIGN KEY (id_cliente)
                REFERENCES clientes(id_cliente)
                ON DELETE CASCADE,

            FOREIGN KEY (id_servico)
                REFERENCES servicos(id)
                ON DELETE CASCADE
        )
    """)

    # Salva as alterações realizadas no banco
    conexao.commit()

    # Encerra a conexão
    conexao.close()

# ==========================================================
# PÁGINA INICIAL
# ==========================================================


@app.route("/")
def home():
    """
    Carrega a página principal do sistema com todos os dados
    necessários para exibição.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    # ------------------------------------------------------
    # CLIENTES
    # ------------------------------------------------------

    cursor.execute("""
    SELECT *
    FROM clientes
    ORDER BY nome ASC
""")
    clientes = cursor.fetchall()

    # ------------------------------------------------------
    # SERVIÇOS
    # ------------------------------------------------------

    cursor.execute("""
    SELECT *
    FROM servicos
    ORDER BY nome ASC
""")
    servicos = cursor.fetchall()

    # ------------------------------------------------------
    # AGENDAMENTOS
    # ------------------------------------------------------
    cursor.execute("""
    SELECT
        a.id_agendamento,
        c.nome,
        s.nome,
        a.forma_pagamento,
        a.data_hora
    FROM agendamentos a
    JOIN clientes c
        ON a.id_cliente = c.id_cliente
    JOIN servicos s
        ON a.id_servico = s.id
    ORDER BY c.nome ASC
""")

    agendamentos = cursor.fetchall()

    # ------------------------------------------------------
    # FATURAMENTO TOTAL
    # ------------------------------------------------------
    cursor.execute("""
        SELECT SUM(s.valor)
        FROM agendamentos a
        JOIN servicos s
            ON a.id_servico = s.id
    """)

    resultado = cursor.fetchone()[0]
    faturamento = resultado if resultado else 0

    # ------------------------------------------------------
    # TOTAL DE AGENDAMENTOS
    # ------------------------------------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM agendamentos
    """)

    total_agendamentos = cursor.fetchone()[0]

    # ------------------------------------------------------
    # CLIENTES ATENDIDOS
    # ------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(DISTINCT id_cliente)
        FROM agendamentos
    """)

    clientes_atendidos = cursor.fetchone()[0]

    # ------------------------------------------------------
    # SERVIÇO MAIS REALIZADO
    # ------------------------------------------------------
    cursor.execute("""
        SELECT
            s.nome,
            COUNT(*)
        FROM agendamentos a
        JOIN servicos s
            ON s.id = a.id_servico
        GROUP BY s.nome
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    mais_servico = cursor.fetchone()

    # ------------------------------------------------------
    # FORMA DE PAGAMENTO MAIS UTILIZADA
    # ------------------------------------------------------
    cursor.execute("""
        SELECT
            forma_pagamento,
            COUNT(*)
        FROM agendamentos
        GROUP BY forma_pagamento
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    mais_pagamento = cursor.fetchone()

    # ------------------------------------------------------
    # DADOS DO RELATÓRIO
    # ------------------------------------------------------

    cursor.execute("""
    SELECT
        c.nome,
        s.nome,
        s.valor,
        a.forma_pagamento,
        a.data_hora
    FROM agendamentos a
    JOIN clientes c
        ON c.id_cliente = a.id_cliente
    JOIN servicos s
        ON s.id = a.id_servico
    ORDER BY c.nome ASC
""")

    dados = cursor.fetchall()

    # Fecha a conexão com o banco
    conexao.close()

    # Renderiza a página principal
    return render_template(
        "index.html",
        clientes=clientes,
        servicos=servicos,
        agendamentos=agendamentos,
        dados=dados,
        faturamento=faturamento,
        total_agendamentos=total_agendamentos,
        clientes_atendidos=clientes_atendidos,
        mais_servico=mais_servico,
        mais_pagamento=mais_pagamento
    )

# ==========================================================
# CADASTRO DE CLIENTES
# ==========================================================


@app.route("/cliente", methods=["POST"])
def cliente():
    """
    Cadastra um novo cliente no banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO clientes (
            nome,
            telefone,
            cpf,
            data_nascimento,
            bairro,
            rua,
            numero_casa,
            cidade,
            estado,
            cep,
            complemento
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        """,
        (
            request.form["nome"],
            request.form["telefone"],
            request.form["cpf"],
            request.form["data_nascimento"],
            request.form["bairro"],
            request.form["rua"],
            request.form["numero_casa"],
            request.form["cidade"],
            request.form["estado"],
            request.form["cep"],
            request.form["complemento"]
        )
    )

    # Salva as alterações no banco de dados
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de clientes
    return redirect("/#clientes")

# ==========================================================
# EXCLUIR CLIENTE
# ==========================================================


@app.route("/delete_cliente/<int:id>")
def delete_cliente(id):
    """
    Exclui um cliente do banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM clientes WHERE id_cliente = %s",
        (id,)
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de clientes
    return redirect("/#clientes")


# ==========================================================
# EDITAR CLIENTE
# ==========================================================

@app.route("/editar_cliente/<int:id>")
def editar_cliente(id):
    """
    Carrega os dados de um cliente para edição.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT * FROM clientes WHERE id_cliente = %s",
        (id,)
    )

    cliente = cursor.fetchone()

    conexao.close()

    return render_template(
        "editar_cliente.html",
        cliente=cliente
    )


# ==========================================================
# ATUALIZAR CLIENTE
# ==========================================================

@app.route("/update_cliente/<int:id>", methods=["POST"])
def update_cliente(id):
    """
    Atualiza os dados de um cliente.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE clientes
        SET
            nome = %s,
            telefone = %s,
            cpf = %s,
            data_nascimento = %s,
            bairro = %s,
            rua = %s,
            numero_casa = %s,
            cidade = %s,
            estado = %s,
            cep = %s,
            complemento = %s
        WHERE id_cliente = %s
        """,
        (
            request.form["nome"],
            request.form["telefone"],
            request.form["cpf"],
            request.form["data_nascimento"],
            request.form["bairro"],
            request.form["rua"],
            request.form["numero_casa"],
            request.form["cidade"],
            request.form["estado"],
            request.form["cep"],
            request.form["complemento"],
            id
        )
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de clientes
    return redirect("/#clientes")

# ==========================================================
# CADASTRO DE SERVIÇOS
# ==========================================================


@app.route("/servico", methods=["POST"])
def servico():
    """
    Cadastra um novo serviço no banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO servicos (
            nome,
            valor
        )
        VALUES (
            %s,
            %s
        )
        """,
        (
            request.form["nome"],
            request.form["valor"]
        )
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de serviços
    return redirect("/#servicos")


# ==========================================================
# EXCLUIR SERVIÇO
# ==========================================================

@app.route("/delete_servico/<int:id>")
def delete_servico(id):
    """
    Remove um serviço do banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM servicos WHERE id = %s",
        (id,)
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de serviços
    return redirect("/#servicos")


# ==========================================================
# EDITAR SERVIÇO
# ==========================================================

@app.route("/editar_servico/<int:id>")
def editar_servico(id):
    """
    Carrega os dados de um serviço para edição.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT * FROM servicos WHERE id = %s",
        (id,)
    )

    servico = cursor.fetchone()

    # Encerra a conexão
    conexao.close()

    return render_template(
        "editar_servico.html",
        servico=servico
    )


# ==========================================================
# ATUALIZAR SERVIÇO
# ==========================================================

@app.route("/update_servico/<int:id>", methods=["POST"])
def update_servico(id):
    """
    Atualiza as informações de um serviço.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE servicos
        SET
            nome = %s,
            valor = %s
        WHERE id = %s
        """,
        (
            request.form["nome"],
            request.form["valor"],
            id
        )
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a página inicial
    return redirect("/")


# ==========================================================
# CADASTRO DE AGENDAMENTOS
# ==========================================================

@app.route("/agendar", methods=["POST"])
def agendar():
    """
    Cadastra um novo agendamento no banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO agendamentos (
            id_cliente,
            id_servico,
            forma_pagamento,
            data_hora
        )
        VALUES (
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            request.form["id_cliente"],
            request.form["id_servico"],
            request.form["forma_pagamento"],
            request.form["data_hora"]
        )
    )

    # Salva as alterações no banco
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a seção de agendamentos
    return redirect("/#agendamentos")
# ==========================================================
# EXCLUIR AGENDAMENTO
# ==========================================================


@app.route("/delete_agendamento/<int:id>")
def delete_agendamento(id):
    """
    Remove um agendamento do banco de dados.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "DELETE FROM agendamentos WHERE id_agendamento = %s",
        (id,)
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a página inicial
    return redirect("/")


# ==========================================================
# EDITAR AGENDAMENTO
# ==========================================================

@app.route("/editar_agendamento/<int:id>")
def editar_agendamento(id):
    """
    Carrega os dados do agendamento para edição.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    # Busca o agendamento selecionado
    cursor.execute(
        "SELECT * FROM agendamentos WHERE id_agendamento = %s",
        (id,)
    )

    agendamento = cursor.fetchone()

    # Carrega os clientes cadastrados
    cursor.execute("""
    SELECT *
    FROM clientes
    ORDER BY nome ASC
""")
    clientes = cursor.fetchall()

    # Carrega os serviços cadastrados
    cursor.execute("""
    SELECT *
    FROM servicos
    ORDER BY nome ASC
""")
    servicos = cursor.fetchall()

    # Encerra a conexão
    conexao.close()

    return render_template(
        "editar_agendamento.html",
        agendamento=agendamento,
        clientes=clientes,
        servicos=servicos
    )


# ==========================================================
# ATUALIZAR AGENDAMENTO
# ==========================================================

@app.route("/update_agendamento/<int:id>", methods=["POST"])
def update_agendamento(id):
    """
    Atualiza as informações de um agendamento.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE agendamentos
        SET
            id_cliente = %s,
            id_servico = %s,
            forma_pagamento = %s,
            data_hora = %s
        WHERE id_agendamento = %s
        """,
        (
            request.form["id_cliente"],
            request.form["id_servico"],
            request.form["forma_pagamento"],
            request.form["data_hora"],
            id
        )
    )

    # Salva as alterações
    conexao.commit()

    # Encerra a conexão
    conexao.close()

    # Retorna para a página inicial
    return redirect("/")


# ==========================================================
# RELATÓRIOS
# ==========================================================

@app.route("/relatorios")
def relatorios():
    """
    Exibe o relatório financeiro com filtros opcionais.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    # ------------------------------------------------------
    # FILTROS RECEBIDOS DO FORMULÁRIO
    # ------------------------------------------------------

    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    cliente = request.args.get("cliente")
    servico = request.args.get("servico")
    pagamento = request.args.get("pagamento")

    # ------------------------------------------------------
    # CONSULTA BASE
    # ------------------------------------------------------

    query = """
        SELECT
            c.nome,
            s.nome,
            s.valor,
            a.forma_pagamento,
            a.data_hora
        FROM agendamentos a
        JOIN clientes c
            ON c.id_cliente = a.id_cliente
        JOIN servicos s
            ON s.id = a.id_servico
        WHERE 1 = 1
    """

    parametros = []

    # ------------------------------------------------------
    # FILTRO POR DATA INICIAL
    # ------------------------------------------------------

    if data_inicio:
        query += " AND DATE(a.data_hora) >= %s"
        parametros.append(data_inicio)

    # ------------------------------------------------------
    # FILTRO POR DATA FINAL
    # ------------------------------------------------------

    if data_fim:
        query += " AND DATE(a.data_hora) <= %s"
        parametros.append(data_fim)

    # ------------------------------------------------------
    # FILTRO POR CLIENTE
    # ------------------------------------------------------

    if cliente:
        query += " AND c.id_cliente = %s"
        parametros.append(cliente)

    # ------------------------------------------------------
    # FILTRO POR SERVIÇO
    # ------------------------------------------------------

    if servico:
        query += " AND s.id = %s"
        parametros.append(servico)

    # ------------------------------------------------------
    # FILTRO POR FORMA DE PAGAMENTO
    # ------------------------------------------------------

    if pagamento:
        query += " AND a.forma_pagamento = %s"
        parametros.append(pagamento)
        query += " ORDER BY c.nome ASC"

    # ------------------------------------------------------
    # EXECUTA A CONSULTA
    # ------------------------------------------------------

    dados = []
    mostrar_tabela = False

    if (
        data_inicio
        or data_fim
        or cliente
        or servico
        or pagamento
    ):
        cursor.execute(query, parametros)
        dados = cursor.fetchall()
        mostrar_tabela = True

    # ------------------------------------------------------
    # RESUMO FINANCEIRO
    # ------------------------------------------------------

    faturamento = sum(float(item[2]) for item in dados) if dados else 0

    total_agendamentos = len(dados)

    clientes_atendidos = len(
        set(item[0] for item in dados)
    )

    # ------------------------------------------------------
    # SERVIÇO MAIS REALIZADO
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            s.nome,
            COUNT(*)
        FROM agendamentos a
        JOIN servicos s
            ON s.id = a.id_servico
        GROUP BY s.nome
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    mais_servico = cursor.fetchone()

    # ------------------------------------------------------
    # FORMA DE PAGAMENTO MAIS UTILIZADA
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            forma_pagamento,
            COUNT(*)
        FROM agendamentos
        GROUP BY forma_pagamento
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    mais_pagamento = cursor.fetchone()

    # ------------------------------------------------------
    # LISTA DE CLIENTES
    # ------------------------------------------------------

    cursor.execute("""
    SELECT *
    FROM clientes
    ORDER BY nome ASC
""")
    clientes = cursor.fetchall()

    # ------------------------------------------------------
    # LISTA DE SERVIÇOS
    # ------------------------------------------------------

    cursor.execute("""
    SELECT *
    FROM servicos
    ORDER BY nome ASC
""")
    servicos = cursor.fetchall()

    # ------------------------------------------------------
    # FINALIZA A CONEXÃO
    # ------------------------------------------------------

    cursor.close()
    conexao.close()

    # ------------------------------------------------------
    # CARREGA A PÁGINA
    # ------------------------------------------------------

    return render_template(
        "index.html",
        clientes=clientes,
        servicos=servicos,
        dados=dados,
        faturamento=faturamento,
        total_agendamentos=total_agendamentos,
        clientes_atendidos=clientes_atendidos,
        mais_servico=mais_servico,
        mais_pagamento=mais_pagamento,
        agendamentos=[],
        mostrar_tabela=mostrar_tabela
    )


# ==========================================================
# EXPORTAR RELATÓRIO PARA EXCEL
# ==========================================================

@app.route("/baixar_relatorio")
def baixar_relatorio():
    """
    Gera e realiza o download do relatório em Excel
    utilizando os filtros selecionados pelo usuário.
    """

    conexao = conectar()

    # ------------------------------------------------------
    # FILTROS RECEBIDOS DO FORMULÁRIO
    # ------------------------------------------------------

    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    cliente = request.args.get("cliente")
    servico = request.args.get("servico")
    pagamento = request.args.get("pagamento")

    # ------------------------------------------------------
    # CONSULTA BASE
    # ------------------------------------------------------

    query = """
        SELECT
            c.nome AS Cliente,
            s.nome AS Servico,
            s.valor AS Valor,
            a.forma_pagamento AS Pagamento,
            a.data_hora AS Data_Hora
        FROM agendamentos a
        JOIN clientes c
            ON a.id_cliente = c.id_cliente
        JOIN servicos s
            ON a.id_servico = s.id
        WHERE 1 = 1
    """

    parametros = []

    # ------------------------------------------------------
    # FILTRO POR DATA INICIAL
    # ------------------------------------------------------

    if data_inicio:
        query += " AND DATE(a.data_hora) >= %s"
        parametros.append(data_inicio)

    # ------------------------------------------------------
    # FILTRO POR DATA FINAL
    # ------------------------------------------------------

    if data_fim:
        query += " AND DATE(a.data_hora) <= %s"
        parametros.append(data_fim)

    # ------------------------------------------------------
    # FILTRO POR CLIENTE
    # ------------------------------------------------------

    if cliente:
        query += " AND c.id_cliente = %s"
        parametros.append(cliente)

    # ------------------------------------------------------
    # FILTRO POR SERVIÇO
    # ------------------------------------------------------

    if servico:
        query += " AND s.id = %s"
        parametros.append(servico)

    # ------------------------------------------------------
    # FILTRO POR FORMA DE PAGAMENTO
    # ------------------------------------------------------

    if pagamento:
        query += " AND a.forma_pagamento = %s"
        parametros.append(pagamento)
        query += " ORDER BY c.nome ASC"

    # ------------------------------------------------------
    # CONSULTA DOS DADOS
    # ------------------------------------------------------

    df = pd.read_sql(
        query,
        conexao,
        params=parametros
    )

    # ------------------------------------------------------
    # FORMATAÇÃO DA DATA
    # ------------------------------------------------------

    if not df.empty:

        df["Data_Hora"] = pd.to_datetime(df["Data_Hora"])

        df["Data_Hora"] = df["Data_Hora"].dt.strftime(
            "%d/%m/%Y %H:%M"
        )

    # ------------------------------------------------------
    # GERAÇÃO DO ARQUIVO EXCEL
    # ------------------------------------------------------

    arquivo = "relatorio_agendamentos.xlsx"

    df.to_excel(
        arquivo,
        index=False
    )
    # ------------------------------------------------------
    # FINALIZA A CONEXÃO
    # ------------------------------------------------------
    conexao.close()

    # ------------------------------------------------------
    # DOWNLOAD DO ARQUIVO
    # ------------------------------------------------------
    return send_file(
        arquivo,
        as_attachment=True
    )


# ==========================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==========================================================

    """
    Ponto de entrada da aplicação.

    Cria as tabelas do banco de dados (caso ainda não existam)
    e inicia o servidor Flask em modo de desenvolvimento.
    """


if __name__ == "__main__":
    criar_tabelas()

    app.run(debug=True)
