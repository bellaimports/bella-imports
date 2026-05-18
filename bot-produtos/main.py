import os
import json
import requests

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from slugify import slugify
from duckduckgo_search import DDGS
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory


DetectorFactory.seed = 0


PASTA_SITE = r"C:\catalogo-loja"

PASTA_IMAGENS_ORIGINAIS = os.path.join(PASTA_SITE, "imagens_originais")
PASTA_IMAGENS_PROCESSADAS = os.path.join(PASTA_SITE, "imagens_processadas")

ARQUIVO_PRODUTOS = os.path.join(PASTA_SITE, "produtos.json")
ARQUIVO_LOGO = os.path.join(PASTA_SITE, "logo.png")


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


def listar_produtos(produtos):
    if not produtos:
        print("\nNenhum produto cadastrado.")
        return False

    print("\nProdutos cadastrados:\n")

    for i, produto in enumerate(produtos):
        nome = produto.get("nome", "Produto sem nome")
        categoria = produto.get("categoria", "Sem categoria")
        preco = produto.get("preco", "Sem preço")

        print(f"{i + 1}. {nome} | {preco} | Categoria: {categoria}")

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


def processar_cores_input(texto):
    """
    Recebe um texto com cores separadas por vírgula e retorna uma lista
    limpa, sem duplicatas e com cada cor capitalizada.
    """
    if not texto or not texto.strip():
        return []

    cores = []

    for parte in texto.split(","):
        cor_limpa = parte.strip()

        if cor_limpa and cor_limpa not in cores:
            # Capitaliza cada palavra (ex: "azul marinho" -> "Azul Marinho")
            cores.append(cor_limpa.title())

    return cores


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
    preco = input("Preço do produto, ou Enter para deixar sem preço: ").strip()

    imagem_url = input(
        "Link direto da imagem ou Enter para buscar automático: "
    ).strip()

    if not imagem_url and nome:
        imagem_url = pesquisar_imagem_na_internet(nome)

    return {
        "url_origem": url,
        "nome": nome if nome else "Produto sem nome",
        "descricao_original": descricao,
        "imagem_url": imagem_url if imagem_url else None,
        "preco": preco
    }


def extrair_dados_generico(url):
    html = baixar_html(url)

    if html is None:
        return cadastrar_produto_manual(url)

    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.find("h1")
    titulo = titulo.get_text(strip=True) if titulo else "Produto sem nome"

    if titulo == "Produto sem nome":
        og_title = soup.find("meta", property="og:title")

        if og_title and og_title.get("content"):
            titulo = og_title["content"].strip()

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

    preco = ""

    meta_price = soup.find("meta", property="product:price:amount")

    if meta_price and meta_price.get("content"):
        preco = meta_price["content"].strip()

    return {
        "url_origem": url,
        "nome": titulo,
        "descricao_original": descricao,
        "imagem_url": imagem_url,
        "preco": preco
    }


def baixar_imagem(imagem_url, nome_produto):
    if not imagem_url:
        print("Nenhuma imagem encontrada.")
        return None

    slug = slugify(nome_produto)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resposta = requests.get(
            imagem_url,
            headers=headers,
            timeout=30
        )

        resposta.raise_for_status()

        content_type = resposta.headers.get(
            "Content-Type",
            ""
        ).lower()

        extensao = ".jpg"

        if "png" in content_type:
            extensao = ".png"

        elif "webp" in content_type:
            extensao = ".webp"

        elif "jpeg" in content_type or "jpg" in content_type:
            extensao = ".jpg"

        caminho = os.path.join(
            PASTA_IMAGENS_ORIGINAIS,
            f"{slug}{extensao}"
        )

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

    saida = os.path.join(
        PASTA_IMAGENS_PROCESSADAS,
        f"{slug}.png"
    )

    try:
        imagem_original = Image.open(caminho_imagem)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError
    ) as erro:
        print("Não foi possível abrir a imagem do produto.")
        print("Motivo:", erro)
        return ""

    if imagem_original.mode != "RGBA":
        imagem_original = imagem_original.convert("RGBA")

    fundo = Image.new(
        "RGB",
        imagem_original.size,
        (255, 255, 255)
    )

    fundo.paste(
        imagem_original,
        mask=imagem_original.split()[3]
    )

    imagem = fundo

    logo = carregar_logo()

    if logo is not None:
        largura_logo = int(imagem.width * 0.16)

        if largura_logo <= 0:
            largura_logo = 80

        proporcao = largura_logo / logo.width
        altura_logo = int(logo.height * proporcao)

        logo = logo.resize(
            (largura_logo, altura_logo)
        )

        margem = int(imagem.width * 0.04)

        posicao = (
            imagem.width - logo.width - margem,
            imagem.height - logo.height - margem
        )

        imagem.paste(
            logo,
            posicao,
            mask=logo
        )

    imagem.save(saida, "PNG")

    return f"imagens_processadas/{slug}.png"


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

    preco_detectado = dados.get("preco", "")

    if preco_detectado:
        print(f"\nPreço detectado: {preco_detectado}")

    preco_manual = input(
        "\nPreço final do produto, ou Enter para manter sem preço: "
    ).strip()

    preco_final = preco_manual if preco_manual else preco_detectado

    caminho_original = baixar_imagem(
        dados["imagem_url"],
        dados["nome"]
    )

    caminho_processado = aplicar_logo_na_imagem(
        caminho_original,
        dados["nome"]
    )

    categoria = input(
        "\nCategoria do produto ou Enter para deixar sem categoria: "
    ).strip()

    cores_input = input(
        "\nCores disponíveis separadas por vírgula (ex: Vermelho, Azul, Preto)\n"
        "ou Enter para produto sem variação de cor: "
    ).strip()

    cores = processar_cores_input(cores_input)

    if cores:
        print(f"Cores cadastradas: {', '.join(cores)}")

    produto_final = {
        "nome": dados["nome"],
        "descricao": gerar_texto_produto(
            dados["nome"],
            dados["descricao_original"]
        ),
        "descricao_original": dados["descricao_original"],
        "preco": preco_final,
        "imagem": caminho_processado,
        "url_origem": dados["url_origem"],
        "categoria": categoria,
        "cores": cores
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

    novo_preco = input(
        f"Preço atual [{produto.get('preco', 'Sem preço')}]: "
    ).strip()

    nova_categoria = input(
        f"Categoria atual [{produto.get('categoria', '')}]: "
    ).strip()

    nova_url = input(
        f"URL origem atual [{produto.get('url_origem', '')}]: "
    ).strip()

    cores_atuais = produto.get("cores", [])
    cores_atuais_str = ", ".join(cores_atuais) if cores_atuais else "Sem cores"

    print(f"\nCores atuais: {cores_atuais_str}")
    print("Digite as novas cores separadas por vírgula, 'limpar' para remover")
    print("todas as cores, ou Enter para manter as atuais.")

    novas_cores_input = input("Cores: ").strip()

    trocar_imagem = input(
        "\nDeseja trocar a imagem? (s/n): "
    ).strip().lower()

    if novo_nome:
        produto["nome"] = novo_nome

    if nova_descricao:
        produto["descricao"] = nova_descricao

    if novo_preco:
        produto["preco"] = novo_preco

    if nova_categoria:
        produto["categoria"] = nova_categoria

    if nova_url:
        produto["url_origem"] = nova_url

    if novas_cores_input:
        if novas_cores_input.lower() == "limpar":
            produto["cores"] = []
            print("Cores removidas.")
        else:
            produto["cores"] = processar_cores_input(novas_cores_input)
            print(f"Cores atualizadas: {', '.join(produto['cores'])}")

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


def detectar_fundo_problematico(caminho_imagem):
    if not caminho_imagem or not os.path.exists(caminho_imagem):
        return False

    try:
        imagem = Image.open(caminho_imagem).convert("RGB")
    except Exception:
        return False

    largura, altura = imagem.size
    pixels = imagem.load()

    amostras = []

    for x in range(0, largura, max(1, largura // 30)):
        amostras.append(pixels[x, 0])
        amostras.append(pixels[x, altura - 1])

    for y in range(0, altura, max(1, altura // 30)):
        amostras.append(pixels[0, y])
        amostras.append(pixels[largura - 1, y])

    escuros = 0

    for r, g, b in amostras:
        if (r + g + b) < 180:
            escuros += 1

    proporcao_escura = escuros / len(amostras)

    return proporcao_escura > 0.4


def reprocessar_imagem_produto(produto):
    nome = produto.get("nome", "produto")
    slug = slugify(nome)

    caminho_original = None

    for extensao in [".jpg", ".png", ".webp", ".jpeg"]:
        candidato = os.path.join(
            PASTA_IMAGENS_ORIGINAIS,
            f"{slug}{extensao}"
        )

        if os.path.exists(candidato):
            caminho_original = candidato
            break

    if not caminho_original:
        url_origem = produto.get("url_origem", "")

        if not url_origem:
            print(f"  Sem URL de origem para baixar de novo. Pulando.")
            return None

        try:
            html = baixar_html(url_origem)

            if html:
                soup = BeautifulSoup(html, "html.parser")
                imagem_meta = soup.find("meta", property="og:image")

                if imagem_meta and imagem_meta.get("content"):
                    caminho_original = baixar_imagem(
                        imagem_meta["content"],
                        nome
                    )
        except Exception as erro:
            print(f"  Erro ao rebaixar imagem: {erro}")
            return None

    if not caminho_original:
        return None

    caminho_processado = aplicar_logo_na_imagem(caminho_original, nome)

    return caminho_processado if caminho_processado else None


def traduzir_se_ingles(texto):
    if not texto or len(texto.strip()) < 10:
        return texto, False

    try:
        idioma = detect(texto)
    except Exception:
        return texto, False

    if idioma != "en":
        return texto, False

    try:
        if len(texto) <= 4500:
            traducao = GoogleTranslator(
                source="en",
                target="pt"
            ).translate(texto)
        else:
            partes = [
                texto[i:i + 4500]
                for i in range(0, len(texto), 4500)
            ]

            traducao = " ".join(
                GoogleTranslator(source="en", target="pt").translate(parte)
                for parte in partes
            )

        return traducao, True

    except Exception as erro:
        print(f"  Erro ao traduzir: {erro}")
        return texto, False


def vistoriar_produtos():
    produtos = carregar_produtos()

    if not produtos:
        print("\nNenhum produto cadastrado para vistoriar.")
        return

    print(f"\nIniciando vistoria de {len(produtos)} produto(s)...\n")

    imagens_corrigidas = 0
    descricoes_traduzidas = 0

    for indice, produto in enumerate(produtos):
        nome = produto.get("nome", "Produto sem nome")
        print(f"[{indice + 1}/{len(produtos)}] {nome}")

        # Garante que o campo cores existe (compatibilidade com produtos antigos)
        if "cores" not in produto:
            produto["cores"] = []

        imagem_relativa = produto.get("imagem", "")

        if imagem_relativa:
            caminho_completo = os.path.join(PASTA_SITE, imagem_relativa)

            if detectar_fundo_problematico(caminho_completo):
                print("  Fundo problemático detectado. Reprocessando...")

                novo_caminho = reprocessar_imagem_produto(produto)

                if novo_caminho:
                    produto["imagem"] = novo_caminho
                    imagens_corrigidas += 1
                    print("  Imagem corrigida.")
                else:
                    print("  Não foi possível corrigir a imagem.")
            else:
                print("  Imagem OK.")

        descricao_original = produto.get("descricao_original", "")

        if not descricao_original:
            descricao_completa = produto.get("descricao", "")

            marcador_inicio = "Informações do produto:\n"
            marcador_fim = "\n\nObservação:"

            if marcador_inicio in descricao_completa and marcador_fim in descricao_completa:
                inicio = descricao_completa.index(marcador_inicio) + len(marcador_inicio)
                fim = descricao_completa.index(marcador_fim)
                descricao_original = descricao_completa[inicio:fim].strip()

                if descricao_original.startswith("- Consulte detalhes"):
                    descricao_original = ""

        if descricao_original:
            texto_traduzido, foi_traduzido = traduzir_se_ingles(descricao_original)

            if foi_traduzido:
                print("  Descrição em inglês detectada. Traduzindo...")

                produto["descricao_original"] = texto_traduzido
                produto["descricao"] = gerar_texto_produto(nome, texto_traduzido)

                descricoes_traduzidas += 1
                print("  Descrição traduzida.")
            else:
                produto["descricao_original"] = descricao_original

    salvar_lista_produtos(produtos)

    print("\n=== Vistoria concluída ===")
    print(f"Imagens corrigidas: {imagens_corrigidas}")
    print(f"Descrições traduzidas: {descricoes_traduzidas}")


def menu():
    print("\n=== BELLA IMPORTS BOT ===\n")
    print("1 - Importar produto")
    print("2 - Deletar produto")
    print("3 - Editar produto")
    print("4 - Vistoriar produtos (consertar imagens e traduzir descrições)")
    print("5 - Sair\n")

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
            vistoriar_produtos()

        elif escolha == "5":
            print("\nEncerrando.")
            break

        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    main()