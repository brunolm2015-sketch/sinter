document.addEventListener("DOMContentLoaded", function () {
    configurarCadastroSenha();
    configurarModalConvenio();
    configurarModalReq();
    configurarModalFormulario();
    abrirAbaPelaUrl();
});

function abrirAbaPelaUrl() {
    const params = new URLSearchParams(window.location.search);
    const aba = params.get("aba");

    if (aba === "formularios") {
        abrirAbaFormularios();
    } else {
        abrirAbaReqs();
    }
}

function configurarCadastroSenha() {
    const senha = document.getElementById("senha");
    const confirmarSenha = document.getElementById("confirmar_senha");
    const mensagemSenha = document.getElementById("mensagemSenha");
    const btnCadastrar = document.getElementById("btnCadastrar");

    if (!senha || !confirmarSenha || !mensagemSenha || !btnCadastrar) {
        return;
    }

    function validarSenhas() {
        if (confirmarSenha.value.length === 0) {
            mensagemSenha.textContent = "";
            btnCadastrar.disabled = false;
            return;
        }

        if (senha.value === confirmarSenha.value) {
            mensagemSenha.textContent = "As senhas estão iguais.";
            mensagemSenha.className = "mensagem-senha senha-ok";
            btnCadastrar.disabled = false;
        } else {
            mensagemSenha.textContent = "As senhas não são iguais.";
            mensagemSenha.className = "mensagem-senha senha-erro";
            btnCadastrar.disabled = true;
        }
    }

    senha.addEventListener("input", validarSenhas);
    confirmarSenha.addEventListener("input", validarSenhas);
}

function configurarModalReq() {
    const abrir = document.getElementById("abrirModalReq");
    const fechar = document.getElementById("fecharModalReq");
    const cancelar = document.getElementById("cancelarModalReq");
    const modal = document.getElementById("modalReq");

    if (abrir) {
        abrir.addEventListener("click", abrirModalNovaReq);
    }

    if (fechar) {
        fechar.addEventListener("click", fecharModalReqFunc);
    }

    if (cancelar) {
        cancelar.addEventListener("click", fecharModalReqFunc);
    }

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                fecharModalReqFunc();
            }
        });
    }
}

function abrirModalNovaReq() {
    const modal = document.getElementById("modalReq");
    const form = document.getElementById("formReq");

    if (!modal || !form) {
        return;
    }

    document.getElementById("tituloModalReq").textContent = "Nova REQ";
    document.getElementById("btnSalvarReq").textContent = "Salvar REQ";

    form.action = "/reqs/nova";
    form.reset();

    modal.classList.add("ativo");
}

function abrirModalEditarReq(id, nome, link) {
    const modal = document.getElementById("modalReq");
    const form = document.getElementById("formReq");

    if (!modal || !form) {
        return;
    }

    document.getElementById("tituloModalReq").textContent = "Editar REQ";
    document.getElementById("btnSalvarReq").textContent = "Salvar Alterações";

    form.action = "/reqs/editar/" + id;

    document.getElementById("req_nome").value = nome;
    document.getElementById("req_link").value = link;

    modal.classList.add("ativo");
}

function fecharModalReqFunc() {
    const modal = document.getElementById("modalReq");

    if (modal) {
        modal.classList.remove("ativo");
    }
}

function configurarModalFormulario() {
    const abrir = document.getElementById("abrirModalFormulario");
    const fechar = document.getElementById("fecharModalFormulario");
    const cancelar = document.getElementById("cancelarModalFormulario");
    const modal = document.getElementById("modalFormulario");

    if (abrir) {
        abrir.addEventListener("click", function () {
            if (modal) {
                modal.classList.add("ativo");
            }
        });
    }

    if (fechar) {
        fechar.addEventListener("click", fecharModalFormularioFunc);
    }

    if (cancelar) {
        cancelar.addEventListener("click", fecharModalFormularioFunc);
    }

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                fecharModalFormularioFunc();
            }
        });
    }
}

function fecharModalFormularioFunc() {
    const modal = document.getElementById("modalFormulario");

    if (modal) {
        modal.classList.remove("ativo");
    }
}

function configurarModalConvenio() {
    const abrir = document.getElementById("abrirModalConvenio");
    const fechar = document.getElementById("fecharModalConvenio");
    const cancelar = document.getElementById("cancelarModalConvenio");
    const modal = document.getElementById("modalConvenio");

    if (abrir) {
        abrir.addEventListener("click", abrirModalNovo);
    }

    if (fechar) {
        fechar.addEventListener("click", fecharModalConvenioFunc);
    }

    if (cancelar) {
        cancelar.addEventListener("click", fecharModalConvenioFunc);
    }

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                fecharModalConvenioFunc();
            }
        });
    }
}

function abrirModalNovo() {
    const modal = document.getElementById("modalConvenio");
    const form = document.getElementById("formConvenio");

    if (!modal || !form) {
        return;
    }

    document.getElementById("tituloModal").textContent = "Novo Convênio";
    document.getElementById("btnSalvarConvenio").textContent = "Salvar Convênio";

    form.action = "/convenios/novo";
    form.reset();

    document.getElementById("imagem_atual").value = "";
    modal.classList.add("ativo");
}

function abrirModalEditar(
    id,
    nome,
    nomeAtivo,
    login,
    loginAtivo,
    cpf,
    cpfAtivo,
    cnpj,
    cnpjAtivo,
    codigo,
    codigoAtivo,
    senha,
    senhaAtivo,
    imagem,
    imagemAtivo
) {
    const modal = document.getElementById("modalConvenio");
    const form = document.getElementById("formConvenio");

    if (!modal || !form) {
        return;
    }

    document.getElementById("tituloModal").textContent = "Editar Convênio";
    document.getElementById("btnSalvarConvenio").textContent = "Salvar Alterações";

    form.action = "/convenios/editar/" + id;

    document.getElementById("nome").value = nome;
    document.getElementById("nome_ativo").checked = nomeAtivo === "True";

    document.getElementById("login").value = login;
    document.getElementById("login_ativo").checked = loginAtivo === "True";

    document.getElementById("cpf").value = cpf;
    document.getElementById("cpf_ativo").checked = cpfAtivo === "True";

    document.getElementById("cnpj").value = cnpj;
    document.getElementById("cnpj_ativo").checked = cnpjAtivo === "True";

    document.getElementById("codigo").value = codigo;
    document.getElementById("codigo_ativo").checked = codigoAtivo === "True";

    document.getElementById("senha_convenio").value = senha;
    document.getElementById("senha_ativo").checked = senhaAtivo === "True";

    document.getElementById("imagem_atual").value = imagem;
    document.getElementById("imagem_ativo").checked = imagemAtivo === "True";

    modal.classList.add("ativo");
}

function fecharModalConvenioFunc() {
    const modal = document.getElementById("modalConvenio");

    if (modal) {
        modal.classList.remove("ativo");
    }
}

function abrirAbaReqs() {
    const abaReqs = document.getElementById("abaReqs");
    const abaFormularios = document.getElementById("abaFormularios");
    const botoes = document.querySelectorAll(".aba-topo");

    if (!abaReqs || !abaFormularios || botoes.length < 2) {
        return;
    }

    abaReqs.style.display = "block";
    abaFormularios.style.display = "none";

    botoes[0].classList.add("ativo");
    botoes[1].classList.remove("ativo");
}

function abrirAbaFormularios() {
    const abaReqs = document.getElementById("abaReqs");
    const abaFormularios = document.getElementById("abaFormularios");
    const botoes = document.querySelectorAll(".aba-topo");

    if (!abaReqs || !abaFormularios || botoes.length < 2) {
        return;
    }

    abaReqs.style.display = "none";
    abaFormularios.style.display = "block";

    botoes[0].classList.remove("ativo");
    botoes[1].classList.add("ativo");
}

function copiarTexto(texto) {
    navigator.clipboard.writeText(texto).then(function () {
        mostrarAvisoCopiado();
    });
}

function mostrarAvisoCopiado() {
    let aviso = document.getElementById("avisoCopiado");

    if (!aviso) {
        aviso = document.createElement("div");
        aviso.id = "avisoCopiado";
        aviso.className = "aviso-copiado";
        aviso.textContent = "Copiado!";
        document.body.appendChild(aviso);
    }

    aviso.classList.add("mostrar");

    setTimeout(function () {
        aviso.classList.remove("mostrar");
    }, 1200);
}