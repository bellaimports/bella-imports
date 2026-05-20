import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

# Permite importar o main.py que está uma pasta acima
PASTA_BOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PASTA_BOT)

from main import (
    criar_pastas,
    carregar_produtos,
    salvar_lista_produtos,
    vistoriar_produtos,
    extrair_dados_generico,
    baixar_imagem,
    aplicar_logo_na_imagem,
    gerar_texto_produto,
    processar_cores_input
)

app = Flask(__name__)
app.secret_key = "troque-esta-chave-secreta"

SENHA_ADMIN = "BBbebelaeventos"


@app.before_request
def preparar():
    criar_pastas()


def logado():
    return session.get("logado") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        senha = request.form.get("senha", "")

        if senha == SENHA_ADMIN:
            session["logado"] = True
            return redirect(url_for("painel"))

        erro = "Senha incorreta."

    return render_template("admin.html", tela="login", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def painel():
    if not logado():
        return redirect(url_for("login"))

    produtos = carregar_produtos()
    return render_template(
        "admin.html",
        tela="painel",
        produtos=produtos,
        mensagem=""
    )


@app.route("/vistoriar", methods=["POST"])
def vistoriar():
    if not logado():
        return redirect(url_for("login"))

    vistoriar_produtos()

    produtos = carregar_produtos()
    return render_template(
        "admin.html",
        tela="painel",
        produtos=produtos,
        mensagem="Vistoria concluída. Produtos verificados, descrições traduzidas quando estavam em inglês e imagens analisadas."
    )


@app.route("/importar", methods=["POST"])
def importar():
    if not logado():
        return redirect(url_for("login"))

    url = request.form.get("url", "").strip()
    preco_manual = request.form.get("preco", "").strip()
    categoria = request.form.get("categoria", "").strip()
    cores_input = request.form.get("cores", "").strip()

    if not url:
        return redirect(url_for("painel"))

    dados = extrair_dados_generico(url)

    preco_detectado = dados.get("preco", "")
    preco_final = preco_manual if preco_manual else preco_detectado

    caminho_original = baixar_imagem(
        dados.get("imagem_url"),
        dados.get("nome", "produto")
    )

    caminho_processado = aplicar_logo_na_imagem(
        caminho_original,
        dados.get("nome", "produto")
    )

    cores = processar_cores_input(cores_input)

    produto_final = {
        "nome": dados.get("nome", "Produto sem nome"),
        "descricao": gerar_texto_produto(
            dados.get("nome", "Produto sem nome"),
            dados.get("descricao_original", "")
        ),
        "descricao_original": dados.get("descricao_original", ""),
        "preco": preco_final,
        "imagem": caminho_processado,
        "url_origem": dados.get("url_origem", url),
        "categoria": categoria,
        "cores": cores
    }

    produtos = carregar_produtos()
    produtos.append(produto_final)
    salvar_lista_produtos(produtos)

    return render_template(
        "admin.html",
        tela="painel",
        produtos=produtos,
        mensagem="Produto importado com sucesso."
    )


@app.route("/deletar/<int:indice>", methods=["POST"])
def deletar(indice):
    if not logado():
        return redirect(url_for("login"))

    produtos = carregar_produtos()

    if 0 <= indice < len(produtos):
        produtos.pop(indice)
        salvar_lista_produtos(produtos)

    return redirect(url_for("painel"))


@app.route("/editar/<int:indice>", methods=["POST"])
def editar(indice):
    if not logado():
        return redirect(url_for("login"))

    produtos = carregar_produtos()

    if 0 <= indice < len(produtos):
        produto = produtos[indice]

        produto["nome"] = request.form.get("nome", produto.get("nome", "")).strip()
        produto["descricao"] = request.form.get("descricao", produto.get("descricao", "")).strip()
        produto["preco"] = request.form.get("preco", produto.get("preco", "")).strip()
        produto["categoria"] = request.form.get("categoria", produto.get("categoria", "")).strip()

        cores_input = request.form.get("cores", "").strip()
        produto["cores"] = processar_cores_input(cores_input)

        produtos[indice] = produto
        salvar_lista_produtos(produtos)

    return redirect(url_for("painel"))

@app.route("/imagens_processadas/<path:nome_arquivo>")
def imagens_processadas(nome_arquivo):
    pasta = r"C:\catalogo-loja\imagens_processadas"
    return send_from_directory(pasta, nome_arquivo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)