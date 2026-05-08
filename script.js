const numeroWhatsApp = "5517999999999";

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const productsGrid = document.getElementById("productsGrid");
const pedidoModal = document.getElementById("pedidoModal");

let produtos = [];
let produtoSelecionado = null;

async function carregarProdutos() {
  try {
    const resposta = await fetch("produtos.json");

    if (!resposta.ok) {
      throw new Error("Não foi possível carregar produtos.json");
    }

    produtos = await resposta.json();
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

  lista.forEach((produto) => {
    const nome = produto.nome || "Produto sem nome";
    const descricao = produto.descricao || "Consulte informações pelo WhatsApp.";
    const categoria = produto.categoria || "sem-categoria";
    const imagem = produto.imagem || "imagens/placeholder-produto.png";

    const card = document.createElement("div");
    card.className = "product-card";
    card.dataset.category = categoria;
    card.dataset.name = nome.toLowerCase();

    card.innerHTML = `
      <img class="product-img" src="${imagem}" alt="${nome}">

      <div class="product-info">
        <span class="category">${formatarCategoria(categoria)}</span>
        <h3>${nome}</h3>
        <p>${descricao}</p>

        <button type="button">
          Pedir produto
        </button>
      </div>
    `;

    card.addEventListener("click", () => abrirModal(produto));

    const botao = card.querySelector("button");

    botao.addEventListener("click", (evento) => {
      evento.stopPropagation();
      abrirModal(produto);
    });

    productsGrid.appendChild(card);
  });
}

function abrirModal(produto) {
  produtoSelecionado = produto;

  const modalProdutoNome = document.getElementById("modalProdutoNome");
  const clienteNome = document.getElementById("clienteNome");
  const clienteCidade = document.getElementById("clienteCidade");
  const clienteEstado = document.getElementById("clienteEstado");

  if (modalProdutoNome) {
    modalProdutoNome.innerText = produto.nome || "Produto";
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

  const nome = document.getElementById("clienteNome")?.value.trim() || "";
  const cidade = document.getElementById("clienteCidade")?.value.trim() || "";
  const estado = document.getElementById("clienteEstado")?.value || "";

  const pagamentoSelecionado = document.querySelector(
    'input[name="formaPagamento"]:checked'
  );

  const pagamento = pagamentoSelecionado
    ? pagamentoSelecionado.value
    : "Não informado";

  if (!nome || !cidade || !estado) {
    alert("Preencha nome, cidade e estado antes de enviar.");
    return;
  }

  const mensagem = `Olá! Gostaria de consultar este produto:

Produto: ${produtoSelecionado.nome}

Dados do cliente:
Nome: ${nome}
Cidade: ${cidade}
Estado: ${estado}

Forma de pagamento escolhida:
${pagamento}

Esse produto está disponível?`;

  const url = `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(mensagem)}`;
  window.open(url, "_blank");

  fecharModal();
}

function formatarCategoria(categoria) {
  return categoria
    .replace("-", " ")
    .replace(/\b\w/g, letra => letra.toUpperCase());
}

function filtrarProdutos() {
  const termo = searchInput.value.toLowerCase().trim();
  const categoria = categoryFilter.value;

  const filtrados = produtos.filter((produto) => {
    const nome = (produto.nome || "").toLowerCase();
    const produtoCategoria = produto.categoria || "sem-categoria";

    const combinaNome = nome.includes(termo);
    const combinaCategoria =
      categoria === "todos" || categoria === produtoCategoria;

    return combinaNome && combinaCategoria;
  });

  renderizarProdutos(filtrados);
}

searchInput.addEventListener("input", filtrarProdutos);
categoryFilter.addEventListener("change", filtrarProdutos);

pedidoModal.addEventListener("click", (evento) => {
  if (evento.target === pedidoModal) {
    fecharModal();
  }
});

document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape") {
    fecharModal();
  }
});

function abrirWhatsAppGeral() {
  const mensagem = "Olá! Gostaria de atendimento na Bella Imports.";
  const url = `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(mensagem)}`;
  window.open(url, "_blank");
}

carregarProdutos();