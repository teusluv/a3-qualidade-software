# Revisão do código

Revisão técnica feita sobre a versão entregue no pacote, **antes** da inspeção da equipe.

> **Atualização de 24/11:** o código ganhou cadastro de curso, anexo de material, botões de voltar e
> limpeza do login com erro. **Atualização de 25/11:** edição e exclusão de curso, edição de
> atividades e perguntas, links de vídeo, eventos paginados, visualização do banco e contas de
> usuário. Os pontos da parte nova são R-20 a R-30.

## Como foi feita

- Leitura de todos os arquivos de `app/` (rotas, serviços, banco, autenticação, templates).
- Ferramentas: `ruff` com regras ampliadas (complexidade, boas práticas, segurança, nomes),
  `bandit`, `vulture` (código morto), `radon` (complexidade) e `pip-audit` (vulnerabilidades
  em dependências).
- Execução do fluxo completo em servidor real, no Chromium (ver `docs/verificacao-do-autor.md`).

## Regra importante sobre estes achados

Os pontos abaixo ficam **abertos de propósito**. A equipe deve:
1. **conferir cada um no código** (não copiar sem verificar);
2. decidir quais viram defeito em `docs/defeitos.md` (com evidência);
3. corrigir, repetir os testes e registrar a regressão, como pede a entrega final.

Corrigir tudo antes da inspeção apagaria o que a atividade pede para mostrar. Posso corrigir
qualquer item depois que a equipe decidir.

## Corrigido durante a revisão

| Item | O que era | O que foi feito |
|---|---|---|
| Dependência | `pypdf 5.9.0` (usado só nos testes) tinha vulnerabilidades conhecidas (`pip-audit`) | Atualizado para 7.1.0; os testes passam e o `pip-audit` não aponta mais nada |
| Dados de demonstração | Em 8 das 10 questões a resposta certa era a letra B: marcar tudo "B" dava 80% e aprovava | Respostas certas redistribuídas (a, b, c, d); marcar tudo "B" agora dá 20% |

## O que está bom

- Regras de negócio isoladas em `services/`, sem Flask, e testadas nos valores limite.
- SQL sempre parametrizado; escape automático nos templates; CSRF e sessão configurados.
- Emissão do certificado e gravação de tentativas atômicas, com teste de concorrência.
- Acesso por perfil e por dono verificado no servidor (e 404 para certificado de outra pessoa).
- Consulta pública devolve o mínimo e rejeita formato inválido sem ecoar a entrada.
- `ruff` e `bandit` sem avisos; `pip-audit` limpo; 100% de cobertura de ramos em `avaliacao.py`.

## Achados abertos

Severidade: **Média** (vale tratar antes de uso real) · **Baixa** (melhoria ou risco pequeno) ·
**Info** (observação).

| ID | Local | Observação | Sev. | Recomendação |
|---|---|---|---|---|
| R-01 | `app/auth.py` (`login`) | Não há limite de tentativas nem bloqueio de conta: dá para testar senhas sem parar (força bruta) | Média | Limitar por matrícula e por IP (ex.: Flask-Limiter) ou atraso progressivo |
| R-02 | `app/__init__.py` | Sem cabeçalhos de segurança (CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) | Média | Acrescentar em um `after_request`; a CSP precisa liberar o `cdn.jsdelivr.net` |
| R-03 | `app/auth.py` (`_autenticar`) | Quando a matrícula não existe, a resposta volta sem calcular o hash: o tempo de resposta pode revelar quais matrículas existem | Baixa | Verificar contra um hash fictício para igualar o tempo |
| R-04 | `app/auth.py` (`logout`) | A sessão fica num cookie assinado; o logout limpa o cookie do navegador, mas um cookie copiado continua válido até expirar (30 min de inatividade) | Baixa | Sessão no servidor ou número de versão da sessão por usuário |
| R-05 | `app/routes/certificados.py` (`verificar`) | A consulta pública não tem limite de requisições e o código vai na URL (fica no histórico do navegador e nos logs do servidor). A entropia do código (128 bits) reduz o risco | Baixa | Limitar requisições; considerar envio por POST |
| R-06 | `app/services/cursos.py` (`concluir_atividade`) | As atividades são autodeclaradas: o colaborador conclui as quatro em segundos, então a regra "100% das atividades" (A-06) não garante estudo | Baixa | Limitação do protótipo; em produção, rastrear conteúdo ou tempo mínimo |
| R-07 | `app/config.py` | `QUESTOES_POR_AVALIACAO` não é usada (a avaliação usa todas as questões do curso): configuração morta que engana | Baixa | Usar de fato ou remover |
| R-08 | `app/services/certificado.py` (`emitir_certificado`) | Complexidade ciclomática 12 (nota C no `radon`) e várias responsabilidades na mesma função | Baixa | Extrair `_verificar_elegibilidade` e `_inserir_com_codigo_unico` |
| R-09 | `app/services/cursos.py` (`registrar_tentativa_se_permitida`) | Seis argumentos posicionais (aviso PLR0917 do ruff): fácil trocar a ordem sem perceber | Baixa | Parâmetros nomeados ou uma estrutura de dados |
| R-10 | `app/routes/cursos.py` (`catalogo`) | Funções (`disponivel`, `progresso`) são passadas ao template: regra de negócio vazando para a visão | Baixa | Calcular na rota e entregar o valor pronto |
| R-11 | `app/auth.py` (`carregar_usuario_logado`) | Roda em todas as requisições, inclusive nos arquivos estáticos, com uma consulta ao banco quando há sessão | Baixa | Ignorar quando `request.endpoint == "static"` |
| R-12 | `app/services/logs.py`, `app/routes/cursos.py` | Datas e horas sem fuso (`datetime.now()`, `date.today()`) | Baixa | Gravar em UTC ou com fuso explícito |
| R-13 | `requirements.txt` | Mistura dependências de execução e de teste/qualidade; uma instalação de produção traria ruff, pytest etc. | Baixa | Separar em `requirements.txt` e `requirements-dev.txt` |
| R-14 | `app/__init__.py` | A falha de CSRF mostra a página 400 padrão, sem orientação ao usuário | Baixa | `errorhandler(CSRFError)` com mensagem amigável |
| R-15 | `app/seed_data.py` | Credenciais de demonstração fixas (`colab123`, `admin123`) no código | Baixa | Nunca rodar o seed em produção; ler a senha do ambiente |
| R-16 | `app/schema.sql` | Datas dos cursos são texto sem restrição de formato; a comparação por texto só funciona com `AAAA-MM-DD` | Baixa | `CHECK` de formato ou tipo/validação na entrada |
| R-17 | `app/services/certificado.py` | `ErroEmissao` não termina em `Error` (aviso N818 do ruff) | Info | Renomear, se a equipe adotar o padrão |
| R-18 | `tests/integration/test_banco_e_seed.py` | Quatro imports dentro de funções (PLC0415) | Info | Mover para o topo do arquivo |
| R-19 | `tests/integration/test_certificado.py` (CT-08) | A medição dos 5 s é feita no serviço, sem passar pelo HTTP; vale para o ambiente local (A-04) | Info | Complementar com medição pela interface no relatório |
| R-20 | `app/services/materiais.py` | O upload confere extensão e assinatura (primeiros bytes) e limita a 20 MB, mas não examina o arquivo inteiro: um PDF ou Office pode trazer macros ou scripts. Não há varredura de vírus nem cota por curso, e os arquivos ficam no disco local | Baixa | Varredura antivírus, cota por curso e armazenamento externo |
| R-21 | `app/services/cadastro.py` | Todo curso novo recebe as 10 questões-modelo e não há tela para editá-las: dois cursos novos têm exatamente a mesma avaliação | Info | Cadastro e edição de questões pela interface |
| R-22 | `app/services/banco.py` | A tela do banco mostra todos os dados (nomes, matrículas, eventos) a qualquer administrador; só o hash da senha fica oculto. Em produção, o acesso a dados pessoais precisaria de justificativa e registro | Baixa | Restringir a poucos perfis e registrar cada consulta |
| R-23 | `app/services/conteudo.py` (`validar_link`) | O link de vídeo só tem o formato validado (http ou https): o sistema não confere se o destino existe nem se é seguro, e o colaborador sai do portal ao clicar | Baixa | Lista de domínios permitidos (YouTube, Teams) |
| R-24 | `app/services/cadastro.py` (`excluir_curso`) | A exclusão de curso é definitiva, sem lixeira. Já é mitigada por bloqueio quando há histórico e pela confirmação digitando o código | Info | Exclusão lógica (marcar como excluído) |
| R-25 | `app/services/banco.py` | Três consultas montam o SQL com nomes de tabela e coluna lidos do próprio banco (nunca da URL direta); o `bandit` aponta B608 e a justificativa está no código (`nosec`). Vale conferir na inspeção | Baixa | Revisar a justificativa; manter os testes de nome malicioso |
| R-26 | `app/routes/usuarios.py` | A senha inicial é definida pelo administrador e repassada à pessoa; **não há troca obrigatória no primeiro acesso** (a pessoa já pode trocar a própria senha em `/conta/senha`) | Baixa | Forçar a troca no primeiro login |
| R-27 | `app/routes/usuarios.py` | **Corrigido em 25/11:** contas agora podem ser desativadas (a conta deixa de entrar e a sessão aberta cai) ou excluídas quando não têm histórico; há proteção contra desativar a própria conta e o último administrador | Corrigido | Tratado por migração automática (`usuario.ativo`) |
| R-28 | `app/services/usuarios.py` | A política de senha é simples (8 a 64 caracteres, uma letra e um número): aceita senhas fracas e comuns, como `senha1234` | Info | Lista de senhas comuns ou exigir mais variedade |
| R-29 | `app/routes/conta.py` | A troca da própria senha exige a senha atual, mas não limita as tentativas erradas: quem roubar uma sessão aberta poderia tentar adivinhá-la (mesmo problema do R-01) | Baixa | Limitar as tentativas, como no login |
| R-30 | `app/services/usuarios.py` | Conta desativada mantém nome, matrícula e setor no banco. A exclusão só vale para quem nunca fez nada; não há anonimização de dados pessoais (LGPD) | Info | Rotina de anonimização após prazo de retenção |

## Resumo

Dois achados foram confirmados por execução (R-11: a consulta ao banco roda também no arquivo
estático; R-14: a falha de CSRF mostra a página 400 padrão em inglês). Um suspeito, o do log de
acesso negado com caminho longo, foi descartado depois de testar: só rotas de administração são
gravadas e uma URL longa dá 404 sem entrar no log.

29 achados abertos: 2 médios, 20 baixos, 7 informativos (e 1 já corrigido, o R-27). Nenhum bloqueia a demonstração do
fluxo principal. Os dois médios (R-01, R-02) são os que mais importariam fora do protótipo.
