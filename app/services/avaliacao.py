"""Regras de nota, aprovação e tentativas (RF-04, RF-05, RF-06, RN-01, RN-02).

Funções puras: não dependem do Flask nem do banco. Por isso são o alvo da cobertura de
decisão do plano (CT-05 e CT-17).
"""

from collections.abc import Iterable, Mapping

from app.config import MAX_TENTATIVAS, NOTA_MINIMA_PADRAO, PERCENTUAL_ATIVIDADES_PARA_AVALIAR

OPCOES_VALIDAS = ("a", "b", "c", "d")


def calcular_nota(acertos: int, total: int) -> int:
    """Percentual de acertos, em número inteiro, truncado.

    O truncamento é proposital: 69,9% nunca pode virar 70% por arredondamento (R-01).
    """
    if total <= 0:
        raise ValueError("O total de questões deve ser maior que zero.")
    if not 0 <= acertos <= total:
        raise ValueError("Os acertos devem estar entre 0 e o total de questões.")
    return acertos * 100 // total


def nota_minima_efetiva(nota_minima_curso: int) -> int:
    """RN-01: o curso pode exigir mais que o padrão, nunca menos."""
    return max(nota_minima_curso, NOTA_MINIMA_PADRAO)


def aprovado(nota: int, nota_minima_curso: int) -> bool:
    """A nota igual ao mínimo aprova (comparação com >=)."""
    return nota >= nota_minima_efetiva(nota_minima_curso)


def contar_acertos(respostas: Mapping[int, str], gabarito: Mapping[int, str]) -> int:
    """Conta acertos. Questão sem resposta ou com opção inválida conta como erro.

    Respostas para questões que não estão no gabarito são ignoradas.
    """
    acertos = 0
    for questao_id, correta in gabarito.items():
        resposta = respostas.get(questao_id)
        if resposta in OPCOES_VALIDAS and resposta == correta:
            acertos += 1
    return acertos


def pode_tentar(tentativas_realizadas: int, maximo: int = MAX_TENTATIVAS) -> bool:
    """A-02 / A-07: o limite vale no total, mesmo após aprovação."""
    return tentativas_realizadas < maximo


def tentativas_restantes(tentativas_realizadas: int, maximo: int = MAX_TENTATIVAS) -> int:
    return max(maximo - tentativas_realizadas, 0)


def maior_nota(notas: Iterable[int]) -> int | None:
    """Vale a maior nota obtida; sem tentativas, não há nota."""
    notas = list(notas)
    return max(notas) if notas else None


def atividades_concluidas(
    concluidas: int, total: int, percentual: int = PERCENTUAL_ATIVIDADES_PARA_AVALIAR
) -> bool:
    """A-06: avaliação liberada quando o percentual exigido de atividades foi concluído."""
    if total <= 0:
        return False
    return concluidas * 100 >= total * percentual


def progresso_percentual(concluidas: int, total: int) -> int:
    """CA-04: 2 de 4 atividades = 50%."""
    if total <= 0:
        return 0
    return concluidas * 100 // total


def elegivel_para_certificado(
    melhor_nota: int | None, nota_minima_curso: int, atividades_ok: bool
) -> bool:
    """RN-02: precisa de atividades concluídas E nota suficiente (CA-09)."""
    if melhor_nota is None or not atividades_ok:
        return False
    return aprovado(melhor_nota, nota_minima_curso)
