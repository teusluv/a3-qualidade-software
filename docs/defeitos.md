# Registro de defeitos

Registre **somente defeitos reais**, encontrados na execução dos testes, na inspeção ou na
análise estática. Cada defeito precisa de evidência (print, saída de comando, trecho de código).

## Escalas

**Severidade** (impacto): Crítica (compromete segurança, dados ou o fluxo principal) · Alta
(funcionalidade importante falha) · Média (falha com alternativa) · Baixa (cosmético ou texto).

**Prioridade** (urgência de correção): P1 (corrigir antes da entrega) · P2 · P3.

**Situação:** Aberto · Corrigido · Verificado (reteste e regressão ok) · Rejeitado (não é defeito).

## Registro

**Execução de 18/11/2026 (Linux, Python 3.13.18):** nenhum defeito funcional foi encontrado.
Na bateria de segurança (OWASP Top 10, 81 verificações, `relatorio-seguranca.md`) também não
houve falha de lógica: os 8 alertas eram de configuração e estão em D-02 a D-04.

**Correção e regressão (18/11/2026, mesma data):** D-02 e D-03 foram corrigidos e verificados.
A bateria de segurança passou de 73/81 para **80/83**, e a suíte foi de 174 para **205 testes**,
todos passando. D-04 continua aberto por ser de implantação, não de código.
174/174 testes automatizados aprovados, `ruff` e `bandit` sem avisos, e os 15 casos executáveis
(CT-01 a CT-13, CT-16, CT-17) terminaram com o resultado esperado. A linha abaixo registra a
única **observação** levantada na execução; ela não impede nenhum fluxo e a equipe decide se
classifica como defeito.

| ID | Título | Onde | Origem (teste, inspeção, estática) | Passos para reproduzir | Esperado × Obtido | Severidade | Prioridade | Evidência | Situação | Correção (commit) | Regressão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D-01 | O código do certificado trafega na URL e fica no histórico do navegador e no log de acesso | `app/templates/verificar.html` (form `method="get"`) e `app/routes/certificados.py:54` | Teste de sistema (CT-11/CT-12) + inspeção | 1. Subir o servidor. 2. Abrir `/verificar`. 3. Consultar um código válido. 4. Ver o log de acesso do servidor e o histórico do navegador. | Esperado: o código, que é o segredo de autenticidade, não ficar registrado fora da consulta. Obtido: a linha `GET /verificar?codigo=CsiG9AlTmYpyfHhSI79BjA` no log de acesso; o código também permanece na URL e no histórico. Nenhum dado pessoal é exposto (CT-12 aprovado) e a consulta funciona normalmente. | Baixa | P3 | `evidencias/D-01-codigo-na-url.txt` | Aberto (a equipe classifica; a correção seria enviar o formulário por POST, ou aceitar o GET e registrar a decisão) | — | — |
| D-02 | Login sem proteção contra força bruta | `app/auth.py` (rota de login) | Teste de segurança (OWASP A04) | 1. Subir o servidor. 2. Enviar 25 tentativas de login com senha errada para a matrícula 1001. | Esperado: atraso, bloqueio temporário ou CAPTCHA após algumas falhas. Obtido: as 25 tentativas foram aceitas em 1,8 s, sem bloqueio e sem atraso. Como a matrícula é só numérica, é previsível. | Média | P2 | Antes: `evidencias/SEG-owasp-top10.txt`. Depois: `evidencias/SEG-owasp-top10-apos-correcao.txt` | **Verificado** | Bloqueio por (origem, matrícula) e por origem em `app/auth.py`, limites em `app/config.py` | Reteste: bloqueou na 6ª tentativa; senha certa também barrada durante o bloqueio; evento `login_bloqueado` no log. 205 testes passando, nenhuma regressão |
| D-03 | Respostas sem cabeçalhos de segurança | `app/__init__.py` (falta um `after_request`) | Teste de segurança (OWASP A05) | 1. Subir o servidor. 2. Olhar os cabeçalhos de qualquer resposta. | Esperado: CSP, X-Frame-Options, X-Content-Type-Options e Referrer-Policy. Obtido: os quatro ausentes. Sem X-Frame-Options a página pode ser embutida em iframe (clickjacking). | Média | P2 | Antes: `evidencias/SEG-owasp-top10.txt`. Depois: `evidencias/D-03-cabecalhos.txt` | **Verificado** | `after_request` em `app/__init__.py` + `CABECALHOS_SEGURANCA` em `app/config.py` | Reteste: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy e Permissions-Policy em toda resposta, inclusive 404 e 403. HSTS só com HTTPS. 31 testes novos | | Servidor anuncia a versão | resposta HTTP, servidor de desenvolvimento | Teste de segurança (OWASP A05) | 1. Subir o servidor. 2. Ler o cabeçalho `Server`. | Esperado: não revelar a pilha. Obtido: `Server: Werkzeug/3.1.9 Python/3.13.18`. Em produção, usar servidor WSGI real atrás de proxy. | Baixa | P3 | `evidencias/D-03-cabecalhos.txt` | **Aberto: correção é de implantação, não de código** | Tentativa descartada: definir `Server` na aplicação só duplicava o cabeçalho, porque quem o emite é o servidor de desenvolvimento, antes da aplicação. A correção é subir atrás de gunicorn/waitress com proxy que remova o cabeçalho | — |
| D-05 | | | | | | | | | | | |

## Regras

- Um defeito por linha; IDs sequenciais (D-01, D-02...).
- Ao corrigir, anote o commit e reexecute o caso que o encontrou **e** os de prioridade alta.
- Defeito rejeitado continua na tabela, com o motivo.
