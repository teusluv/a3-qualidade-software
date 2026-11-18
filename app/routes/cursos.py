"""Catálogo, curso, atividades, avaliação e histórico (T-02, T-03, T-04, RF-02 a RF-06, RF-10)."""

from datetime import date

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import login_required
from app.config import MAX_TENTATIVAS
from app.db import get_db
from app.services import avaliacao, cursos
from app.services.logs import registrar

bp = Blueprint("cursos", __name__)


def _curso_visivel_ou_404(curso_id: int):
    """Devolve o resumo do curso para o usuário logado, ou 404.

    Cursos de outro setor e cursos arquivados (sem histórico do usuário) não aparecem.
    """
    resumo = cursos.obter_resumo(get_db(), g.usuario["id"], curso_id)
    if resumo is None:
        abort(404)
    if resumo["inscricao_id"] is None:
        fora_do_setor = resumo["setor"] not in (None, g.usuario["setor"])
        if resumo["status"] == "arquivado" or fora_do_setor:
            abort(404)
    return resumo


def _estado_do_curso(resumo) -> dict:
    """Regras calculadas no servidor para decidir o que a tela pode oferecer."""
    arquivado = resumo["status"] == "arquivado"
    atividades_ok = avaliacao.atividades_concluidas(
        resumo["concluidas"], resumo["total_atividades"]
    )
    iniciado = resumo["inscricao_id"] is not None
    return {
        "iniciado": iniciado,
        "arquivado": arquivado,
        "pode_iniciar": not iniciado
        and cursos.curso_aceita_novo_inicio(
            resumo["status"], resumo["data_inicio"], resumo["data_fim"], date.today()
        ),
        "atividades_ok": atividades_ok,
        "pode_avaliar": iniciado
        and not arquivado
        and atividades_ok
        and avaliacao.pode_tentar(resumo["tentativas"]),
        "tentativas_restantes": avaliacao.tentativas_restantes(resumo["tentativas"]),
        "progresso": avaliacao.progresso_percentual(
            resumo["concluidas"], resumo["total_atividades"]
        ),
        "elegivel_certificado": avaliacao.elegivel_para_certificado(
            resumo["melhor_nota"], resumo["nota_minima"], atividades_ok
        ),
    }


@bp.get("/")
@login_required
def raiz():
    return redirect(url_for("cursos.catalogo"))


@bp.get("/cursos")
@login_required
def catalogo():
    itens = cursos.listar_catalogo(get_db(), g.usuario["id"], g.usuario["setor"])
    hoje = date.today()
    return render_template(
        "catalogo.html",
        itens=itens,
        disponivel=lambda c: cursos.curso_aceita_novo_inicio(
            c["status"], c["data_inicio"], c["data_fim"], hoje
        ),
        progresso=avaliacao.progresso_percentual,
    )


@bp.get("/historico")
@login_required
def historico():
    itens = cursos.listar_historico(get_db(), g.usuario["id"])
    return render_template("historico.html", itens=itens)


@bp.get("/cursos/<int:curso_id>")
@login_required
def detalhe(curso_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    atividades = cursos.listar_atividades(get_db(), curso_id, resumo["inscricao_id"])
    return render_template(
        "curso.html",
        curso=resumo,
        atividades=atividades,
        estado=_estado_do_curso(resumo),
        max_tentativas=MAX_TENTATIVAS,
    )


@bp.post("/cursos/<int:curso_id>/iniciar")
@login_required
def iniciar(curso_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    estado = _estado_do_curso(resumo)
    db = get_db()
    if estado["iniciado"]:
        return redirect(url_for("cursos.detalhe", curso_id=curso_id))
    if not estado["pode_iniciar"]:
        registrar(db, "inicio_bloqueado", g.usuario["id"], f"curso={resumo['codigo']}")
        db.commit()
        flash("Este curso não aceita novos inícios (suspenso ou fora do período).", "warning")
        return redirect(url_for("cursos.detalhe", curso_id=curso_id))

    cursos.iniciar_curso(db, g.usuario["id"], curso_id)
    registrar(db, "curso_iniciado", g.usuario["id"], f"curso={resumo['codigo']}")
    db.commit()
    flash("Curso iniciado.", "success")
    return redirect(url_for("cursos.detalhe", curso_id=curso_id))


@bp.post("/cursos/<int:curso_id>/atividades/<int:atividade_id>/concluir")
@login_required
def concluir_atividade(curso_id: int, atividade_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    estado = _estado_do_curso(resumo)
    if not estado["iniciado"]:
        flash("Inicie o curso antes de concluir atividades.", "warning")
    elif estado["arquivado"]:
        flash("Este curso foi arquivado; só o histórico está disponível.", "warning")
    else:
        db = get_db()
        if cursos.concluir_atividade(db, resumo["inscricao_id"], curso_id, atividade_id):
            registrar(db, "atividade_concluida", g.usuario["id"], f"curso={resumo['codigo']}")
            db.commit()
        else:
            abort(404)
    return redirect(url_for("cursos.detalhe", curso_id=curso_id))


def _avaliacao_liberada_ou_redirecionar(resumo, curso_id: int):
    """Devolve None se pode avaliar; senão, o redirecionamento com a mensagem."""
    estado = _estado_do_curso(resumo)
    if not estado["iniciado"]:
        mensagem = "Inicie o curso antes de fazer a avaliação."
    elif estado["arquivado"]:
        mensagem = "Este curso foi arquivado; não é possível fazer a avaliação."
    elif not estado["atividades_ok"]:
        mensagem = "Conclua todas as atividades para liberar a avaliação."
    elif not estado["pode_avaliar"]:
        mensagem = f"Limite de {MAX_TENTATIVAS} tentativas atingido."
    else:
        return None
    flash(mensagem, "warning")
    return redirect(url_for("cursos.detalhe", curso_id=curso_id))


@bp.get("/cursos/<int:curso_id>/avaliacao")
@login_required
def avaliacao_form(curso_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    bloqueio = _avaliacao_liberada_ou_redirecionar(resumo, curso_id)
    if bloqueio:
        return bloqueio
    return render_template(
        "avaliacao.html",
        curso=resumo,
        questoes=cursos.listar_questoes(get_db(), curso_id),
        numero_tentativa=resumo["tentativas"] + 1,
        max_tentativas=MAX_TENTATIVAS,
    )


@bp.post("/cursos/<int:curso_id>/avaliacao")
@login_required
def avaliacao_enviar(curso_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    bloqueio = _avaliacao_liberada_ou_redirecionar(resumo, curso_id)  # validação no servidor
    if bloqueio:
        return bloqueio

    db = get_db()
    gabarito = cursos.obter_gabarito(db, curso_id)
    if not gabarito:
        flash("Este curso ainda não tem avaliação cadastrada.", "warning")
        return redirect(url_for("cursos.detalhe", curso_id=curso_id))

    respostas = {qid: request.form.get(f"q{qid}", "") for qid in gabarito}
    acertos = avaliacao.contar_acertos(respostas, gabarito)
    total = len(gabarito)
    nota = avaliacao.calcular_nota(acertos, total)
    tentativa_id = cursos.registrar_tentativa_se_permitida(
        db, resumo["inscricao_id"], acertos, total, nota, MAX_TENTATIVAS
    )
    if tentativa_id is None:  # outro envio ocupou a última tentativa neste meio tempo
        flash(f"Limite de {MAX_TENTATIVAS} tentativas atingido.", "warning")
        return redirect(url_for("cursos.detalhe", curso_id=curso_id))
    registrar(
        db, "avaliacao_realizada", g.usuario["id"], f"curso={resumo['codigo']} nota={nota}"
    )
    db.commit()
    return redirect(url_for("cursos.resultado", curso_id=curso_id, tentativa_id=tentativa_id))


@bp.get("/cursos/<int:curso_id>/resultado/<int:tentativa_id>")
@login_required
def resultado(curso_id: int, tentativa_id: int):
    resumo = _curso_visivel_ou_404(curso_id)
    tentativa = cursos.obter_tentativa(get_db(), tentativa_id, g.usuario["id"], curso_id)
    if tentativa is None:
        abort(404)
    return render_template(
        "resultado.html",
        curso=resumo,
        tentativa=tentativa,
        aprovado=avaliacao.aprovado(tentativa["nota"], resumo["nota_minima"]),
        estado=_estado_do_curso(resumo),
        nota_minima=avaliacao.nota_minima_efetiva(resumo["nota_minima"]),
    )
