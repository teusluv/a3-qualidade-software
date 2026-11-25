# Divisão de tarefas e cronograma

## Atualização de 24/11 (véspera da entrega 1): prioridades de hoje

1. **Hoje à noite:** todos rodam o projeto (`README`, seção 2) e conferem que os testes passam.
2. **Hoje:** executar os casos de prioridade alta e registrar resultado e evidência em
   `docs/execucao-testes.md` (pelo menos CT-01, 02, 05, 06, 07, 09, 11, 12, 16, 17).
3. **Hoje:** rodar `ruff` e `bandit`, registrar a saída em `docs/inspecao.md` e `docs/evidencias/`.
4. **Hoje:** registrar em `docs/defeitos.md` o que **vocês encontraram** (com print), por exemplo: falta
   de botão de voltar, falta de onde anexar o material, campos do login não limpos após erro (já
   corrigidos nesta versão: registrem o defeito, a correção e a regressão).
5. **Manhã de 25/11:** conferir tudo, montar o documento e entregar.

O cronograma abaixo foi escrito em 17/11 e fica como referência para a entrega final.

Sugestão de divisão para os cinco integrantes. **Troquem à vontade**: o importante é que
cada tarefa tenha um dono e que as revisões sejam cruzadas (ninguém inspeciona só o que fez).

Datas: hoje é 17/11/2026 (terça). Entrega 1 em **25/11 (quarta)**; entrega final em **02/12 (quarta)**.

## 1. Papéis sugeridos

| Integrante | Papel principal | Tarefas |
|---|---|---|
| Alan Souza Sampaio | Ambiente e integração | Repositório no GitHub, CI verde, versão congelada (tag), conferir que o pacote roda do zero; execução de CT-01, CT-02, CT-16 |
| Felipe Augusto Mendes Evangelista | Testes de caixa-preta | CT-05, CT-06, CT-07, CT-09 pela interface, com prints e registro |
| Guilherme da Silva Melo | Testes de segurança e caixa-branca | CT-11, CT-12, CT-10, CT-17 (cobertura), análise estática (ruff e bandit) |
| José Mateus Santos Nunes | Inspeção do código | Checklist de `docs/inspecao.md`, achados com local e evidência; revisar `docs/revisao-de-codigo.md` |
| Marcos Messias Menezes de Almeida | Documentação e apresentação | Registro de defeitos, relatório, avaliação de critérios, slides; CT-14 e CT-15 (Lighthouse, teclado, navegadores) com apoio de quem tiver os navegadores |

Revisão cruzada: cada pessoa confere os registros de outra antes de fechar o documento.

## 2. Cronograma até a entrega 1 (25/11)

| Data | O que fazer | Responsável |
|---|---|---|
| 17 e 18/11 (ter, qua) | Cada um instala e roda o projeto (README, "Começo rápido"); subir no GitHub e confirmar o CI | Todos; Alan lidera |
| 19/11 (qui) | Reunião curta: distribuir os casos de teste e combinar o modelo de evidência (pasta e nomes de arquivo) | Todos |
| 19 a 21/11 (qui a sáb) | Executar os casos de prioridade alta; rodar ruff, bandit e cobertura; começar a inspeção | Felipe, Guilherme, Alan, José |
| 22 e 23/11 (dom, seg) | Registrar defeitos reais com evidência; classificar severidade; fechar a inspeção | José, Marcos |
| 24/11 (ter) | Revisão cruzada; congelar a versão (tag); montar o documento da entrega | Todos; Marcos consolida |
| 25/11 (qua) | **Entrega 1** | Todos |

## 3. Cronograma até a entrega final (02/12)

| Data | O que fazer | Responsável |
|---|---|---|
| 26 a 28/11 (qui a sáb) | Corrigir os defeitos (por severidade); casos de prioridade média (CT-03, CT-04, CT-13, CT-14, CT-15) | Quem achou o defeito corrige com apoio; Marcos nos manuais |
| 29 e 30/11 (dom, seg) | Regressão: repetir os casos de prioridade alta e os afetados; atualizar o registro de execução | Felipe, Guilherme, Alan |
| 30/11 (seg) | Avaliar CA-01 a CA-17 e os atributos (`docs/avaliacao-criterios.md`); revisar a proposta de CI/CD | Marcos, José |
| 1/12 (ter) | Ensaiar a apresentação e a demonstração do fluxo principal; congelar a versão final | Todos |
| 2/12 (qua) | **Entrega final e apresentação** | Todos |

## 4. Regras do time

- Uma branch por pessoa e tarefa (`nome/tarefa`); merge só por pull request com CI verde e uma revisão.
- Defeito entra em `docs/defeitos.md` **com evidência**; defeito sem evidência não entra.
- Teste não executado entra como "Não executado", com o motivo. Nunca omitir.
- Qualquer mudança no código depois do congelamento exige regressão e registro.
- Combinem um canal único para dúvidas e um responsável por consolidar o documento final.

## 5. Riscos do cronograma

| Risco | O que fazer |
|---|---|
| Alguém não consegue rodar o projeto | Ver "Problemas comuns" no README; se persistir, pedir ajuda no dia 18/11, não depois |
| Poucos defeitos encontrados | Registrar os que existem; não inventar. A inspeção e a revisão do código trazem pontos reais para analisar |
| Lighthouse ou navegadores indisponíveis | Registrar "Não executado" com o motivo e o plano de execução |
| Mudança de última hora no código | Evitar depois de 24/11; se necessário, rodar `pytest` e registrar a regressão |
