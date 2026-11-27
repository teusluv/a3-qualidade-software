# Verificação feita pelo autor do código

Este documento registra o que foi **realmente executado** antes da entrega do código e, com a
mesma clareza, o que **não** foi verificado. Ele não substitui a execução da equipe
(`docs/execucao-testes.md`): a equipe deve repetir os testes no seu ambiente.

## 1. Ambiente da verificação

- Python 3.12, Linux; ambiente virtual novo, instalado **só** pelo `requirements.txt`.
- Servidor real (`flask --app app run`) com o banco criado pelo `python seed.py`.
- Navegador: Chromium 153 sem interface (Playwright), em 1280 px e em 360 px.
- O Bootstrap foi servido de um arquivo local, porque o ambiente de verificação não acessa a
  internet. O arquivo é o mesmo do pacote oficial 5.3.3 (o hash de integridade do `base.html`
  confere com ele).

## 2. Resultados

| Verificação | Resultado |
|---|---|
| Testes automatizados (`pytest`) | 440 testes passam |
| `ruff check .` e `bandit -r app` | Sem avisos |
| Cobertura de ramos | 96% em `app/`; 100% em `app/services/avaliacao.py` |
| Fluxo completo no navegador | 43 verificações passam (lista abaixo), mais 21 do roteiro das telas (cadastro, anexo, botões de voltar, login com erro) 34 do roteiro de gestão (editar curso e código, atividades, perguntas e respostas, links, exclusão, eventos paginados, banco de dados) 10 do roteiro de contas (criar conta, senha, perfil) e 19 do roteiro de situação das contas (desativar, reativar, trocar a própria senha), mais a migração de um banco antigo real |
| Acessibilidade automática (axe-core) | 0 violações em 18 páginas, após as correções da seção 3 |
| Tela de 360 px | Sem rolagem horizontal em 7 páginas |
| Log do servidor durante o fluxo | Nenhum erro |

**Fluxo percorrido no navegador:** login inválido e vazio; login só com o teclado; catálogo
(obrigatório, setor, suspenso e arquivado); curso suspenso com botão desabilitado; início do
curso; progresso de 50%; avaliação bloqueada até concluir as atividades; avaliação com 8
acertos (80%); download do PDF e leitura dos campos; histórico; limite de 3 tentativas e
bloqueio por URL direta; consulta pública (autêntico, inexistente, entradas maliciosas);
acesso negado ao `/admin/` para colaborador; painel do administrador e alteração de situação do
curso; logout.

## 3. Problemas encontrados e corrigidos durante a verificação

1. **Envios simultâneos da avaliação** podiam ultrapassar o limite de 3 tentativas (a checagem e
   a gravação não eram atômicas). Agora ocorrem na mesma transação; há teste de concorrência.
2. **Servidor sem `seed.py`**: o banco ficava sem tabelas e a primeira página dava erro 500. Agora
   as tabelas são criadas e o terminal avisa para rodar `python seed.py`.
3. **Banco da versão anterior** (sem a coluna `concluido_em`) causaria erro só na emissão. Agora
   o servidor recusa na partida, com a instrução "apague a pasta `instance`".
4. **Erro 500** mostrava a página padrão; agora mostra uma mensagem amigável, sem detalhes internos.
5. **Menu em 360 px** quebrava o layout; agora os links ficam em linha e quebram de forma limpa.
6. **Contraste insuficiente** nos links do menu e nos botões de contorno (apontado pelo axe-core).
7. **Botão "Voltar" cinza** com contraste insuficiente (axe-core) e **link `javascript:`** no "Voltar" da página de erro; trocado por um link real que usa a página anterior do próprio sistema.
8. **Nas telas de gestão:** contraste dos trechos de código (`code`), dois blocos de paginação com o mesmo rótulo e um cabeçalho de tabela vazio (axe-core).
9. **Tela de contas em celular de 360 px** alargava a página: rótulos invisíveis dentro de tabela escapavam da rolagem da tabela. Corrigido no CSS.
10. **Banco da versão anterior sem a coluna `ativo`:** o sistema agora acrescenta a coluna sozinho, sem apagar dados (testado com um banco antigo real).

## 4. O que NÃO foi verificado

- **Lighthouse** (CT-14): não foi executado; só se mediu a carga local da página de login (cerca de
  0,1 s, sem internet e sem rede real).
- **Outros navegadores** (CT-15): só Chromium. Firefox e Edge ficam para a equipe.
- **Aparelho celular real**: só a simulação de 360 px.
- **Teclado em todo o fluxo**: só login e envio de formulários foram feitos pelo teclado; o resto
  usou cliques. A ordem de tabulação completa e o foco visível devem ser conferidos à mão.
- **Python 3.11** e **Windows**: não testados (a verificação foi em Python 3.12, Linux).
- **GitHub Actions**: o pipeline foi escrito, mas não rodou no GitHub.
- **Carga** (500 acessos) e **disponibilidade**: fora do escopo do protótipo.
- **CDN real**: o carregamento do Bootstrap pela internet não foi exercitado.

Estar sem defeitos conhecidos não é o mesmo que ser livre de defeitos: a inspeção e a execução
da equipe continuam necessárias, e qualquer defeito real deve ir para `docs/defeitos.md`.

## 5. Capturas de referência

`docs/referencia-interface/` traz capturas de como as telas ficaram no ambiente do autor. Servem
para comparar com o que a equipe vê; **não** são evidência de execução da equipe.
