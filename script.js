const numeroWhatsApp = "5517997332057";

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const productsGrid = document.getElementById("productsGrid");
const pedidoModal = document.getElementById("pedidoModal");

let produtos = [];
let produtoSelecionado = null;
let corSelecionada = "";

async function carregarProdutos() {

  try {

    const resposta = await fetch("produtos.json");

    if (!resposta.ok) {
      throw new Error("Não foi possível carregar produtos.json");
    }

    produtos = await resposta.json();

    carregarCategoriasDinamicas();

    renderizarProdutos(produtos);

  } catch (erro) {

    productsGrid.innerHTML = `
      <div class="empty-message">
        <p>Erro ao carregar produtos.</p>
        <small>Verifique se o arquivo produtos.json existe.</small>
      </div>
    `;

    console.error("Erro ao carregar produtos:", erro);
  }

}

function carregarCategoriasDinamicas() {

  categoryFilter.innerHTML = `
    <option value="todos">
      Todas as categorias
    </option>
  `;

  const categorias = [];

  produtos.forEach((produto) => {

    const categoria = produto.categoria;

    if (
      categoria &&
      categoria.trim() !== "" &&
      !categorias.includes(categoria)
    ) {
      categorias.push(categoria);
    }

  });

  categorias.sort();

  categorias.forEach((categoria) => {

    const option = document.createElement("option");

    option.value = categoria;
    option.textContent = categoria;

    categoryFilter.appendChild(option);

  });

}

function renderizarProdutos(lista) {

  productsGrid.innerHTML = "";

  if (!lista || lista.length === 0) {

    productsGrid.innerHTML = `
      <div class="empty-message">
        <p>Nenhum produto encontrado.</p>
      </div>
    `;

    return;
  }

  lista.forEach((produto, indiceProduto) => {

    const nome =
      produto.nome || "Produto sem nome";

    const descricao =
      produto.descricao ||
      "Consulte informações pelo WhatsApp.";

    const categoria =
      produto.categoria || "Sem categoria";

    const imagemBase =
      produto.imagem ||
      "imagens/placeholder-produto.png";

    const imagem = produto.imagem
      ? `${imagemBase}?v=${Date.now()}`
      : imagemBase;

    const preco =
      produto.preco || "";

    const cores = Array.isArray(produto.cores) ? produto.cores : [];

    const card = document.createElement("div");

    card.className = "product-card";

    card.dataset.category = categoria;
    card.dataset.name = nome.toLowerCase();
    card.dataset.indice = indiceProduto;

    // Monta o seletor de cores apenas se o produto tem cores
    let blocoSeletorCor = "";

    if (cores.length > 0) {

      const opcoesCor = cores
        .map((cor) => `<option value="${cor}">${cor}</option>`)
        .join("");

      blocoSeletorCor = `
        <div class="color-selector">
          <label class="color-label">
            Escolha a cor
          </label>

          <select class="color-select">
            <option value="">
              Selecione...
            </option>
            ${opcoesCor}
          </select>
        </div>
      `;

    }

    card.innerHTML = `
      <img
        class="product-img"
        src="${imagem}"
        alt="${nome}"
      >

      <div class="product-info">

        <span class="category">
          ${categoria}
        </span>

        <h3>${nome}</h3>

        ${
          preco
            ? `<div class="product-price">${preco}</div>`
            : ""
        }

        <p>${descricao}</p>

        ${blocoSeletorCor}

        <button type="button">
          Pedir produto
        </button>

      </div>
    `;

    // Impede que cliques no seletor de cor abram o modal
    const colorSelect = card.querySelector(".color-select");

    if (colorSelect) {

      colorSelect.addEventListener("click", (evento) => {
        evento.stopPropagation();
      });

      colorSelect.addEventListener("change", (evento) => {
        evento.stopPropagation();
      });

    }

    card.addEventListener(
      "click",
      () => {

        const corEscolhida =
          colorSelect ? colorSelect.value : "";

        abrirModal(produto, corEscolhida, card);
      }
    );

    const botao = card.querySelector("button");

    botao.addEventListener("click", (evento) => {

      evento.stopPropagation();

      const corEscolhida =
        colorSelect ? colorSelect.value : "";

      abrirModal(produto, corEscolhida, card);

    });

    productsGrid.appendChild(card);

  });

}

function abrirModal(produto, cor, card) {

  // Se o produto tem cores cadastradas, exige escolha antes de abrir
  const temCores =
    Array.isArray(produto.cores) && produto.cores.length > 0;

  if (temCores && !cor) {

    alert(
      "Por favor, escolha uma cor antes de pedir o produto."
    );

    // Destaca o seletor brevemente
    if (card) {

      const seletor = card.querySelector(".color-selector");

      if (seletor) {
        seletor.classList.add("color-selector-aviso");

        setTimeout(() => {
          seletor.classList.remove("color-selector-aviso");
        }, 1500);
      }

    }

    return;
  }

  produtoSelecionado = produto;
  corSelecionada = cor || "";

  const modalProdutoNome =
    document.getElementById("modalProdutoNome");

  const clienteNome =
    document.getElementById("clienteNome");

  const clienteCidade =
    document.getElementById("clienteCidade");

  const clienteEstado =
    document.getElementById("clienteEstado");

  if (modalProdutoNome) {

    const nomeExibido = corSelecionada
      ? `${produto.nome || "Produto"} - ${corSelecionada}`
      : produto.nome || "Produto";

    modalProdutoNome.innerText = nomeExibido;
  }

  if (clienteNome) {
    clienteNome.value = "";
  }

  if (clienteCidade) {
    clienteCidade.value = "";
  }

  if (clienteEstado) {
    clienteEstado.value = "";
  }

  const pixRadio = document.querySelector(
    'input[name="formaPagamento"][value="PIX"]'
  );

  if (pixRadio) {
    pixRadio.checked = true;
  }

  pedidoModal.classList.add("ativo");

}

function fecharModal() {

  pedidoModal.classList.remove("ativo");

}

function enviarPedidoWhatsApp() {

  if (!produtoSelecionado) return;

  const nome =
    document.getElementById("clienteNome")
    ?.value
    .trim() || "";

  const cidade =
    document.getElementById("clienteCidade")
    ?.value
    .trim() || "";

  const estado =
    document.getElementById("clienteEstado")
    ?.value || "";

  const pagamentoSelecionado =
    document.querySelector(
      'input[name="formaPagamento"]:checked'
    );

  const pagamento =
    pagamentoSelecionado
      ? pagamentoSelecionado.value
      : "Não informado";

  if (!nome || !cidade || !estado) {

    alert(
      "Preencha nome, cidade e estado antes de enviar."
    );

    return;
  }

  const preco =
    produtoSelecionado.preco
      ? `Preço informado no site: ${produtoSelecionado.preco}\n`
      : "";

  // Inclui a cor no nome do produto, se houver
  const nomeProdutoMensagem = corSelecionada
    ? `${produtoSelecionado.nome} - Cor: ${corSelecionada}`
    : produtoSelecionado.nome;

  const mensagem = `Olá! Gostaria de consultar este produto:

Produto: ${nomeProdutoMensagem}
${preco}
Dados do cliente:
Nome: ${nome}
Cidade: ${cidade}
Estado: ${estado}

Forma de pagamento escolhida:
${pagamento}

Esse produto está disponível?`;

  const url =
    `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(mensagem)}`;

  window.open(url, "_blank");

  fecharModal();

}

function filtrarProdutos() {

  const termo =
    searchInput.value
      .toLowerCase()
      .trim();

  const categoria =
    categoryFilter.value;

  const filtrados = produtos.filter((produto) => {

    const nome =
      (produto.nome || "")
        .toLowerCase();

    const produtoCategoria =
      produto.categoria || "";

    const combinaNome =
      nome.includes(termo);

    const combinaCategoria =
      categoria === "todos" ||
      categoria === produtoCategoria;

    return (
      combinaNome &&
      combinaCategoria
    );

  });

  renderizarProdutos(filtrados);

}

searchInput.addEventListener(
  "input",
  filtrarProdutos
);

categoryFilter.addEventListener(
  "change",
  filtrarProdutos
);

pedidoModal.addEventListener(
  "click",
  (evento) => {

    if (evento.target === pedidoModal) {
      fecharModal();
    }

  }
);

document.addEventListener(
  "keydown",
  (evento) => {

    if (evento.key === "Escape") {
      fecharModal();
    }

  }
);

function abrirWhatsAppGeral() {

  const mensagem =
    "Olá! Gostaria de atendimento na Bella Imports.";

  const url =
    `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(mensagem)}`;

  window.open(url, "_blank");

}

carregarProdutos();