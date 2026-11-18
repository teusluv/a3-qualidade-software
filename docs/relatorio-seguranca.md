# Relatório de testes de segurança — 18/11/2026

Bateria própria no padrão **OWASP Top 10 (2021)**, executada contra o portal rodando em
`127.0.0.1:5000`, com banco recém-semeado. Saída completa em `evidencias/SEG-owasp-top10.txt`.

**Resultado inicial: 81 verificações · 73 passaram · 8 alertas, todos de configuração.**
**Depois das correções (seção 4): 83 verificações · 80 passaram · 3 alertas, todos dependentes
de HTTPS ou do servidor de produção.**

Nenhuma falha permitiu entrar sem senha, ver dado de outra pessoa, alterar nota ou emitir
certificado indevido.

## 1. O que passou

| Categoria OWASP | Verificações | O que foi tentado e não funcionou |
|---|---|---|
| A01 Controle de acesso | 14 | Anônimo em `/cursos`, `/historico`, `/admin/`, `/cursos/1` e no PDF: todos devolvem 302 para `/login`. Colaborador em `/admin/`: 403. IDOR no PDF de outro colaborador: 404. Resultado de avaliação alheia: 404. Curso de outro setor (1002 da Farmácia no curso de Enfermagem): 404, inclusive no POST de início. Sem open redirect pelo parâmetro `next`. |
| A02 Falhas criptográficas | 8 | Senhas em scrypt; nenhuma em texto puro. Código do certificado com 22 caracteres aleatórios, sem repetição. Cookie com HttpOnly e SameSite. Consulta pública sem matrícula e com nome mascarado. |
| A03 Injeção | 21 | 5 payloads de SQL injection no login (todos 401); SQLi cega por tempo (0,01 s, sem atraso); `'; DROP TABLE certificado; --` na verificação (400, tabela intacta); 4 payloads de XSS refletido; 4 de XSS no campo de matrícula (todos escapados: `&#34;`, `&lt;`); 4 de SSTI (`{{7*7}}` não vira 49, `{{config.SECRET_KEY}}` não vaza); 3 de path traversal. |
| A04/A07 Autenticação e sessão | 9 | Cookie de sessão é renovado no login (sem session fixation). Logout invalida a sessão. POST sem token CSRF: 400, em login, início de curso e emissão. Token CSRF de uma sessão recusado em outra: 400. |
| A05 Configuração | 9 | 404 sem rastro de pilha. Debugger fechado. `/instance/portal.db`, `/.git/config`, `/.env`, `/app/config.py` e listagem de `/static/`: todos 404. |
| A08 Integridade da regra de negócio | 6 | Campos extras `nota=100`, `aprovado=1` e `acertos=10` enviados junto com a avaliação: ignorados, a nota veio do servidor. Questões `q0` e `q11` fora do gabarito: ignoradas. Situação de curso inválida: 400. Curso inexistente no admin: 404. Atividade de outro curso: 404. |
| A09 Registro | 3 | 36 eventos de falha e negação registrados; nenhum detalhe guarda senha ou o que foi digitado. |

## 2. Alertas (todos de configuração)

Os dois primeiros já constavam como **limitações conhecidas** no README e em
`revisao-de-codigo.md`. A novidade aqui é a **medição**, com evidência.

| ID | Alerta | Medição | Severidade | Correção sugerida |
|---|---|---|---|---|
| S-01 | Sem proteção contra força bruta no login | 25 senhas erradas seguidas em **1,8 s**, sem bloqueio, sem atraso e sem CAPTCHA | **Média** (num hospital, uma matrícula é previsível: só números) | Atraso progressivo ou bloqueio temporário por matrícula e por IP, mais alerta no log após N falhas |
| S-02 | Cabeçalhos de segurança ausentes | CSP, X-Frame-Options, X-Content-Type-Options e Referrer-Policy não vêm em nenhuma resposta | **Média** (sem X-Frame-Options a página pode ser aberta em iframe: clickjacking) | Um `@app.after_request` que acrescenta os quatro cabeçalhos |
| S-03 | O servidor anuncia versão | `Server: Werkzeug/3.1.9 Python/3.13.18` | **Baixa** | Em produção, servidor WSGI real (gunicorn/waitress) atrás de proxy, com o cabeçalho removido |
| S-04 | Cookie sem `Secure` e sem HSTS | Esperado: o protótipo roda em HTTP local | **Informativo** | Em HTTPS, `SESSION_COOKIE_SECURE=1` e HSTS. Já previsto no `config.py` |

## 3. Três falsos positivos encontrados e descartados

Registrados porque ensinam a ler resultado de teste de segurança:

1. **"Anônimo baixa o PDF: HTTP 200".** Era o cliente do teste seguindo o redirecionamento: o
   servidor devolvia 302 para `/login`, e o 200 era da tela de login. Refeito sem seguir
   redirecionamento: 302, correto.
2. **"Curso de outro setor abre: HTTP 200".** O teste usava o usuário 1001, que é da Enfermagem,
   contra o curso B, que é da Enfermagem. Refeito com o 1002, da Farmácia: 404, correto.
3. **"XSS no login".** O payload aparecia no HTML, mas escapado pelo Jinja
   (`value="&#34;&gt;&lt;script&gt;..."`), que é o comportamento certo. Confirmado com três
   payloads que quebram atributo.

## 4. Correção e reteste (mesma data)

S-01 e S-02 foram corrigidos e a bateria foi reexecutada: **83 verificações, 80 passaram.**
Evidência em `evidencias/SEG-owasp-top10-apos-correcao.txt` e `evidencias/D-03-cabecalhos.txt`.

| ID | O que mudou | Onde | Reteste |
|---|---|---|---|
| S-01 / D-02 | Contagem de falhas por (origem, matrícula) e por origem, com janela de 10 min e bloqueio de 5 min. Resposta 429 com mensagem igual para qualquer matrícula, para não revelar quais existem. Evento `login_bloqueado` no log, sem guardar o que foi digitado | `app/auth.py`, limites em `app/config.py` | Bloqueou na **6ª** tentativa; 20 das 25 recusadas com 429; a senha correta também é barrada durante o bloqueio |
| S-02 / D-03 | `after_request` acrescenta CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy e Permissions-Policy a **toda** resposta, inclusive 404 e 403. HSTS só quando o cookie é `Secure` (HTTPS) | `app/__init__.py`, valores em `app/config.py` | Os cinco cabeçalhos presentes em todas as páginas testadas |

Duas decisões que valem registro:

1. **CSP com `'unsafe-inline'` só para estilo.** As barras de progresso usam `style="width: X%"`.
   Script embutido não existe em nenhuma página, então `script-src` ficou sem `'unsafe-inline'`,
   que é o que realmente importa contra XSS.
2. **`Referrer-Policy: no-referrer` também reduz o D-01.** Como o código do certificado vai na
   URL da verificação, essa política impede que ele saia no cabeçalho `Referer` para o CDN.

### S-03 não foi corrigido, e o motivo importa

Tentei definir `Server: Portal` na aplicação. O resultado foi o cabeçalho **duplicado**: o
servidor de desenvolvimento do Flask emite o dele antes da aplicação responder. Desfiz a
mudança. O cabeçalho não é da aplicação, é do servidor: a correção é subir atrás de um servidor
WSGI real (gunicorn, waitress) com um proxy que remova o cabeçalho. Fica registrado como
**aberto, de implantação**, e não como código por corrigir.

## 5. Conclusão

A camada de código resistiu a tudo que foi tentado: injeção, adulteração de parâmetro, acesso
indevido e falsificação de requisição. Os dois alertas de configuração que dependiam do código
foram corrigidos, com 31 testes novos para impedir que voltem, e a regressão completa (205
testes) passou sem nenhuma quebra. Restam apenas itens de implantação: HSTS e cookie `Secure`
(que dependem de HTTPS) e o cabeçalho `Server` (que depende do servidor de produção).
