"""Dados fictícios de demonstração. Usado por seed.py e pelos testes.

É repetível: pode ser executado várias vezes sem duplicar registros, porque cada
inserção respeita as chaves UNIQUE do schema.
"""

from datetime import date, timedelta

from werkzeug.security import generate_password_hash

USUARIOS = [
    # matrícula, nome, senha, perfil, setor
    ("1001", "Carla Mendes Lima", "colab123", "colaborador", "Enfermagem"),
    ("1002", "Rafael Santos Oliveira", "colab123", "colaborador", "Farmácia"),
    ("9001", "Administrador do Portal", "admin123", "administrador", "TI"),
]

# Período vigente relativo a hoje, para os cursos ativos não "vencerem" com o tempo.
_INICIO = (date.today() - timedelta(days=180)).isoformat()
_FIM = (date.today() + timedelta(days=365)).isoformat()

CURSOS = [
    # código, título, carga, nota mínima, obrigatório, setor, status, início, fim
    ("A", "Segurança do Paciente", 4, 70, 1, None, "ativo", _INICIO, _FIM),
    ("B", "Higienização das Mãos e Controle de Infecção", 6, 80, 0, "Enfermagem",
     "ativo", _INICIO, _FIM),
    ("C", "Biossegurança em Laboratório", 4, 70, 0, None, "suspenso", _INICIO, _FIM),
    ("D", "Protocolo Antigo de Triagem", 3, 70, 0, None, "arquivado", "2024-01-01", "2025-12-31"),
]

ATIVIDADES = [
    "Leitura do material de apoio",
    "Vídeo explicativo",
    "Estudo de caso",
    "Checklist de boas práticas",
]

# enunciado, A, B, C, D, correta (as letras certas variam de propósito)
QUESTOES = [
    ('Qual é o momento correto de higienizar as mãos?',
     'Apenas ao final do plantão',
     'Somente quando estiverem visivelmente sujas',
     'Antes e depois do contato com o paciente',
     'Uma vez por turno',
     'c'),
    ('O que deve ser conferido antes de administrar um medicamento?',
     'Paciente, medicamento, dose, via e horário',
     'Somente o nome do medicamento',
     'Apenas a embalagem',
     'Só a prescrição do dia anterior',
     'a'),
    ('Como identificar corretamente um paciente?',
     'Pelo número do leito',
     'Pelo nome informado pelo acompanhante',
     'Pela aparência',
     'Por pelo menos dois identificadores, como nome e data de nascimento',
     'd'),
    ('Qual atitude previne quedas de pacientes?',
     'Deixar o piso molhado',
     'Manter grades e campainha ao alcance, quando indicado',
     'Retirar a pulseira de risco',
     'Evitar orientar o paciente',
     'b'),
    ('O que fazer ao identificar um incidente no cuidado?',
     'Ocultar para evitar problemas',
     'Comentar apenas com colegas',
     'Esperar o paciente reclamar',
     'Registrar e notificar pelo canal institucional',
     'd'),
    ('Onde devem ser descartados materiais perfurocortantes?',
     'Em coletor rígido próprio para perfurocortantes',
     'No lixo comum',
     'Em sacos plásticos comuns',
     'Na pia',
     'a'),
    ('Qual é a finalidade do uso de equipamentos de proteção individual?',
     'Apenas seguir a norma',
     'Substituir a higienização das mãos',
     'Reduzir o risco de exposição a agentes biológicos',
     'Identificar o setor',
     'c'),
    ('Informações do prontuário podem ser compartilhadas com:',
     'Qualquer pessoa interessada',
     'Apenas profissionais envolvidos no cuidado, conforme a necessidade',
     'Visitantes em geral',
     'Redes sociais',
     'b'),
    ('Qual é o primeiro passo ao suspeitar de reação adversa?',
     'Interromper o procedimento e comunicar a equipe responsável',
     'Ignorar os sintomas',
     'Aguardar o fim do turno',
     'Alterar a prescrição por conta própria',
     'a'),
    ('A comunicação segura entre equipes inclui:',
     'Recados informais',
     'Anotações sem identificação',
     'Informações apenas verbais sem registro',
     'Passagem de plantão estruturada e registro claro',
     'd'),
]


def carregar_dados(db) -> None:
    """Insere usuários, cursos, atividades e questões de demonstração."""
    for matricula, nome, senha, perfil, setor in USUARIOS:
        existe = db.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matricula,)).fetchone()
        if existe is None:  # só calcula o hash quando vai inserir
            db.execute(
                "INSERT INTO usuario (matricula, nome, senha_hash, perfil, setor) "
                "VALUES (?, ?, ?, ?, ?)",
                (matricula, nome, generate_password_hash(senha), perfil, setor),
            )

    for curso in CURSOS:
        db.execute(
            "INSERT OR IGNORE INTO curso (codigo, titulo, carga_horaria, nota_minima, obrigatorio, "
            "setor, status, data_inicio, data_fim) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            curso,
        )

    for (curso_id,) in db.execute("SELECT id FROM curso").fetchall():
        for ordem, titulo in enumerate(ATIVIDADES, start=1):
            db.execute(
                "INSERT OR IGNORE INTO atividade (curso_id, ordem, titulo) VALUES (?, ?, ?)",
                (curso_id, ordem, titulo),
            )
        for ordem, questao in enumerate(QUESTOES, start=1):
            db.execute(
                "INSERT OR IGNORE INTO questao (curso_id, ordem, enunciado, opcao_a, opcao_b, "
                "opcao_c, opcao_d, correta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (curso_id, ordem, *questao),
            )
    db.commit()
