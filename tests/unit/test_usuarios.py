"""Caixa-branca: validação de contas e senhas."""

import pytest

from app.services.usuarios import validar_senha, validar_usuario

VALIDO = {"matricula": "2001", "nome": "Maria da Silva", "setor": "Farmácia", "perfil": "colaborador", "senha": "senha1234"}


def _com(**mudancas):
    return {**VALIDO, **mudancas}


def test_conta_valida():
    limpo, erros = validar_usuario(VALIDO)

    assert erros == []
    assert limpo == {"matricula": "2001", "nome": "Maria da Silva", "setor": "Farmácia", "perfil": "colaborador"}
    assert "senha" not in limpo  # a senha não vai junto dos dados da conta


def test_espacos_extras_sao_normalizados():
    limpo, _ = validar_usuario(_com(nome="  Maria   da  Silva ", setor=" Farmácia  "))

    assert limpo["nome"] == "Maria da Silva"
    assert limpo["setor"] == "Farmácia"


@pytest.mark.parametrize("matricula", ["", "12", "12345678901", "abc123", "12 34", "12.34", "１２３４"])
def test_matricula_invalida(matricula):
    _, erros = validar_usuario(_com(matricula=matricula))

    assert any("Matrícula" in e for e in erros)


@pytest.mark.parametrize("matricula", ["123", "1234567890"])
def test_matricula_nos_limites_e_aceita(matricula):
    _, erros = validar_usuario(_com(matricula=matricula))

    assert erros == []


@pytest.mark.parametrize("campo", ["nome", "setor"])
@pytest.mark.parametrize("valor", ["", "a", "  "])
def test_nome_e_setor_curtos_demais(campo, valor):
    _, erros = validar_usuario(_com(**{campo: valor}))

    assert any(campo.capitalize() in e for e in erros)


@pytest.mark.parametrize("perfil", ["", "admin", "gestor", "ADMINISTRADOR"])
def test_perfil_invalido(perfil):
    _, erros = validar_usuario(_com(perfil=perfil))

    assert any("Perfil" in e for e in erros)


@pytest.mark.parametrize("senha", ["", "abc12", "abcdefgh", "12345678", "a1" * 33])
def test_senha_fraca_ou_fora_do_tamanho(senha):
    assert validar_senha(senha) != []


@pytest.mark.parametrize("senha", ["abcd1234", "SENHA2026", "colab123", "a1" * 32])
def test_senha_aceita(senha):
    assert validar_senha(senha) == []


def test_senha_none_e_recusada():
    assert validar_senha(None) != []


# ---------- troca da própria senha ----------

from werkzeug.security import generate_password_hash  # noqa: E402

from app.services.usuarios import validar_troca_senha  # noqa: E402

HASH_ATUAL = generate_password_hash("senhaAtual1")


def test_troca_valida():
    assert validar_troca_senha(HASH_ATUAL, "senhaAtual1", "senhaNova22", "senhaNova22") == []


def test_senha_atual_errada():
    erros = validar_troca_senha(HASH_ATUAL, "errada123", "senhaNova22", "senhaNova22")

    assert erros == ["Senha atual: não confere."]


def test_senha_atual_vazia_ou_none():
    assert validar_troca_senha(HASH_ATUAL, "", "senhaNova22", "senhaNova22") != []
    assert validar_troca_senha(HASH_ATUAL, None, "senhaNova22", "senhaNova22") != []


def test_nova_senha_fraca():
    erros = validar_troca_senha(HASH_ATUAL, "senhaAtual1", "curta1", "curta1")

    assert any("Senha:" in e for e in erros)


def test_nova_senha_igual_a_atual():
    erros = validar_troca_senha(HASH_ATUAL, "senhaAtual1", "senhaAtual1", "senhaAtual1")

    assert any("diferente da atual" in e for e in erros)


def test_confirmacao_diferente():
    erros = validar_troca_senha(HASH_ATUAL, "senhaAtual1", "senhaNova22", "senhaNova23")

    assert any("Confirmação" in e for e in erros)
