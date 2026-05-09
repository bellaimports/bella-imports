import os
import json
import requests

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from slugify import slugify
from duckduckgo_search import DDGS


# =========================
# CONFIGURAÇÕES
# =========================

PASTA_SITE = r"C:\catalogo-loja"

PASTA_IMAGENS_ORIGINAIS = "imagens_originais"
PASTA_IMAGENS_PROCESSADAS = os.path.join(PASTA_SITE, "imagens_processadas")

ARQUIVO_PRODUTOS = os.path.join(PASTA_SITE, "produtos.json")
ARQUIVO_LOGO = "logo.png"


# =========================
# PASTAS E JSON
# =========================

def criar_pastas():
    os.makedirs(PASTA_IMAGENS_ORIGINAIS, exist_ok=True)
    os.makedirs(PASTA_IMAGENS_PROCESSADAS, exist_ok=True)

    if not os.path.exists(ARQUIVO_PRODUTOS):
        with open(ARQUIVO_PRODUTOS, "w", encoding="utf-8") as arquivo:
            json.dump([], arquivo, indent=2, ensure_ascii=False)


def carregar_produtos():
    if not os.path.exists(ARQUIVO_PRODUTOS):
        return []

    with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as arquivo:
        try:
            return json.load(arquivo)
        except json.JSONDecodeError:
            return []


def salvar_lista_produtos(produtos):
    with open(ARQUIVO_PRODUTOS, "w", encoding="utf-8") as arquivo:
        json.dump(produtos, arquivo, indent=2, ensure_ascii=False)


# =========================
# LISTAGEM
# =========================

def listar_produtos(produtos):
    if not produtos:
        print("\nNenhum produto cadastrado.")
        return False

    print("\nProdutos cadastrados:\n")

    for i, produto in enumerate(produtos):
        nome = produto.get("nome", "Produto sem nome")
        categoria = produto.get("categoria", "sem-categoria")
        print(f"{i + 1}. {nome} | Categoria: {categoria}")

    return True


def escolher_produto(produtos):
    if not listar_produtos(produtos):
        return None

    try:
        escolha = int(input("\nNúmero do produto: ")) - 1
    except ValueError:
        print("Número inválido.")
        return None

    if escolha < 0 or escolha >= len(produtos):
        print("Produto inválido.")
        return None

    return escolha


# =========================
# SCRAPING
# =========================

def baixar_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }

    resposta = requests.get(url, headers=headers, timeout=25)

    if resposta.status_code == 403:
        return None

    resposta.raise_for_status()
    return resposta.text


def pesquisar_imagem_na_internet(nome_produto):
    print("\nBuscando imagem automaticamente...")

    try:
        termo = f"{nome_produto} product official image white background"

        with DDGS() as ddgs:
            resultados = list(ddgs.images(
                termo,
                max_results=8,
                safesearch="moderate"
            ))

        for item in resultados:
            imagem_url = item.get("image")

            if imagem_url:
                print("Imagem encontrada:")
                print(imagem_url)
                return imagem_url

    except Exception as erro:
        print("Erro ao buscar imagem.")
        print("Motivo:", erro)

    return None


def cadastrar_produto_manual(url):
    print("\nModo manual ativado.\n")

    nome = input("Nome do produto: ").strip()
    descricao = input("Descrição curta do produto: ").strip()

    imagem_url = input(
        "Link direto da imagem ou Enter para buscar automático: "
    ).strip()

    if not imagem_url and nome:
        imagem_url = pesquisar_imagem_na_internet(nome)

    return {
        "url_origem": url,
        "nome": nome if nome else "Produto sem nome",
        "descricao_original": descricao,
        "imagem_url": imagem_url if imagem_url else None
    }


def extrair_dados_generico(url):
    html = baixar_html(url)

    if html is None:
        return cadastrar_produto_manual(url)

    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.find("h1")
    titulo = titulo.get_text(strip=True) if titulo else "Produto sem nome"

    meta_description = soup.find("meta", attrs={"name": "description"})
    descricao = (
        meta_description["content"].strip()
        if meta_description and meta_description.get("content")
        else ""
    )

    imagem = soup.find("meta", property="og:image")
    imagem_url = (
        imagem["content"]
        if imagem and imagem.get("content")
        else None
    )

    if titulo == "Produto sem nome":
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            titulo = og_title["content"].strip()

    return {
        "url_origem": url,
        "nome": titulo,
        "descricao_original": descricao,
        "imagem_url": imagem_url
    }


# =========================
# IMAGENS
# =========================

def baixar_imagem(imagem_url, nome_produto):
    if not imagem_url:
        print("Nenhuma imagem encontrada.")
        return None

    slug = slugify(nome_produto)
    caminho = os.path.join(PASTA_IMAGENS_ORIGINAIS, f"{slug}.jpg")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resposta = requests.get(imagem_url, headers=headers, timeout=30)
        resposta.raise_for_status()

        with open(caminho, "wb") as arquivo:
            arquivo.write(resposta.content)

        return caminho

    except Exception as erro:
        print("Não foi possível baixar a imagem.")
        print("Motivo:", erro)
        return None


def carregar_logo():
    if not os.path.exists(ARQUIVO_LOGO):
        print("Logo não encontrada. Produto será salvo sem marca d'água.")
        return None

    try:
        return Image.open(ARQUIVO_LOGO).convert("RGBA")
    except Exception as erro:
        print("Não foi possível abrir a logo.png.")
        print("Motivo:", erro)
        return None


def aplicar_logo_na_imagem(caminho_imagem, nome_produto):
    if not caminho_imagem:
        return ""

    slug = slugify(nome_produto)
    saida = os.path.join(PASTA_IMAGENS_PROCESSADAS, f"{slug}.png")

    try:
        imagem = Image.open(caminho_imagem).convert("RGBA")
    except (UnidentifiedImageError, OSError, ValueError) as erro:
        print("Não foi possível abrir a imagem do produto.")
        print("Motivo:", erro)
        return ""

    logo = carregar_logo()

    if logo is None:
        imagem.convert("RGB").save(saida)
        return f"imagens_processadas/{slug}.png"

    largura_logo = int(imagem.width * 0.16)

    if largura_logo <= 0:
        largura_logo = 80

    proporcao = largura_logo / logo.width
    altura_logo = int(logo.height * proporcao)

    logo = logo.resize((largura_logo, altura_logo))

    margem = int(imagem.width * 0.04)

    posicao = (
        imagem.width - logo.width - margem,
        imagem.height - logo.height - margem
    )

    camada = Image.new("RGBA", imagem.size, (255, 255, 255, 0))
    camada.paste(logo, posicao, logo)

    resultado = Image.alpha_composite(imagem, camada)
    resultado.convert("RGB").save(saida)

    return f"imagens_processadas/{slug}.png"


# =========================
# PRODUTO
# =========================

def gerar_texto_produto(nome, descricao_original):
    return f"""
{nome}

Produto selecionado pela Bella Imports.

Informações do produto:
{descricao_original if descricao_original else "- Consulte detalhes pelo WhatsApp."}

Observação:
Disponibilidade e condições devem ser confirmadas antes da compra.
""".strip()


def salvar_produto(produto):
    produtos = carregar_produtos()
    produtos.append(produto)
    salvar_lista_produtos(produtos)


def importar_produto(url):
    print("\nImportando produto:")
    print(url)

    dados = extrair_dados_generico(url)

    print("\nNome encontrado:")
    print(dados["nome"])

    caminho_original = baixar_imagem(
        dados["imagem_url"],
        dados["nome"]
    )

    caminho_processado = aplicar_logo_na_imagem(
        caminho_original,
        dados["nome"]
    )

    categoria = input(
        "\nCategoria do produto ou Enter para sem-categoria: "
    ).strip()

    produto_final = {
        "nome": dados["nome"],
        "descricao": gerar_texto_produto(
            dados["nome"],
            dados["descricao_original"]
        ),
        "imagem": caminho_processado,
        "url_origem": dados["url_origem"],
        "categoria": categoria if categoria else "sem-categoria"
    }

    salvar_produto(produto_final)

    print("\nProduto salvo com sucesso.")


def deletar_produto():
    produtos = carregar_produtos()
    indice = escolher_produto(produtos)

    if indice is None:
        return

    produto = produtos.pop(indice)
    imagem = produto.get("imagem", "")

    if imagem:
        caminho_imagem = os.path.join(PASTA_SITE, imagem)

        if os.path.exists(caminho_imagem):
            try:
                os.remove(caminho_imagem)
            except Exception:
                pass

    salvar_lista_produtos(produtos)

    print("\nProduto removido:")
    print(produto.get("nome", "Produto sem nome"))


def editar_produto():
    produtos = carregar_produtos()
    indice = escolher_produto(produtos)

    if indice is None:
        return

    produto = produtos[indice]

    print("\nEditando produto:")
    print(produto.get("nome", "Produto sem nome"))

    print("\nDeixe em branco para manter o valor atual.\n")

    novo_nome = input(
        f"Nome atual [{produto.get('nome', '')}]: "
    ).strip()

    nova_descricao = input(
        "Nova descrição: "
    ).strip()

    nova_categoria = input(
        f"Categoria atual [{produto.get('categoria', 'sem-categoria')}]: "
    ).strip()

    nova_url = input(
        f"URL origem atual [{produto.get('url_origem', '')}]: "
    ).strip()

    trocar_imagem = input(
        "Deseja trocar a imagem? (s/n): "
    ).strip().lower()

    if novo_nome:
        produto["nome"] = novo_nome

    if nova_descricao:
        produto["descricao"] = nova_descricao

    if nova_categoria:
        produto["categoria"] = nova_categoria

    if nova_url:
        produto["url_origem"] = nova_url

    if trocar_imagem == "s":
        imagem_url = input(
            "Link direto da nova imagem ou Enter para buscar automático: "
        ).strip()

        if not imagem_url:
            imagem_url = pesquisar_imagem_na_internet(
                produto.get("nome", "produto")
            )

        caminho_original = baixar_imagem(
            imagem_url,
            produto.get("nome", "produto")
        )

        caminho_processado = aplicar_logo_na_imagem(
            caminho_original,
            produto.get("nome", "produto")
        )

        if caminho_processado:
            imagem_antiga = produto.get("imagem", "")

            if imagem_antiga:
                caminho_antigo = os.path.join(PASTA_SITE, imagem_antiga)

                if os.path.exists(caminho_antigo):
                    try:
                        os.remove(caminho_antigo)
                    except Exception:
                        pass

            produto["imagem"] = caminho_processado

    produtos[indice] = produto
    salvar_lista_produtos(produtos)

    print("\nProduto atualizado com sucesso.")


# =========================
# MENU
# =========================

def menu():
    print("\n=== BELLA IMPORTS BOT ===\n")
    print("1 - Importar produto")
    print("2 - Deletar produto")
    print("3 - Editar produto")
    print("4 - Sair\n")

    return input("Escolha: ").strip()


def main():
    criar_pastas()

    while True:
        escolha = menu()

        if escolha == "1":
            url = input("\nCole o link do produto: ").strip()

            if url:
                importar_produto(url)

        elif escolha == "2":
            deletar_produto()

        elif escolha == "3":
            editar_produto()

        elif escolha == "4":
            print("\nEncerrando.")
            break

        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    main()