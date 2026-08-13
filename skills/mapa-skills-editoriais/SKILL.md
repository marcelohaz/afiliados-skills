---
name: mapa-skills-editoriais
description: Mapa de qual skill usar para cada objeto editorial (bíblia, página de produto, review em artigo, intro, guia, meta, categoria, institucionais) e por que o fluxo roda via Skill tool em vez dos botões do painel. Invoque quando estiver em dúvida sobre QUAL skill chamar, ou quando precisar dos pré-requisitos de painel de cada uma (stub criado, bíblia preenchida). Não substitui as skills em si — é o índice delas.
---

### IA editorial — preencher / auditar via Skill tool (não painel)

**Quando o user pedir "preenche X", "audita X" pra bíblia ou página individual
de produto:**

1. SEMPRE invocar a Skill tool ANTES de qualquer outra ação. Padrão de nomes:
   `<objeto>-[<sub>-]<ação>`. Skills aceitam URL do painel OU args canônicos.

   **⚠ Vale TAMBÉM quando user invoca via slash-command** (`/biblia-preencher X`).
   O slash-command carrega a SKILL.md inline na conversa, e há tentação de
   simplesmente executar manualmente os passos lidos. **Não execute manualmente.**

   **Use SEMPRE o namespace `afiliados-skills:*`** ao invocar via Skill tool —
   nunca o namespace `{hash}:*` (cache pinned no Mac específico).

   ```
   ✓ Skill(skill="afiliados-skills:biblia-preencher", args="X")  ← marketplace, latest, Bárbara também tem
   ✗ Skill(skill="16ca9ac1fa0f:biblia-preencher", args="X")     ← cache pinned, só Marcelo tem
   ```

   **Por quê 2 namespaces?**
   - `{hash}:*` = cache local pinned a uma versão (ex: `16ca9ac1fa0f` = v1.3.0 do meu install em 2026-05-19)
   - `afiliados-skills:*` = marketplace dir (atualiza via `/plugin marketplace update`)

   Bárbara não tem o hash `16ca9ac1fa0f` — ela tem o próprio hash do install dela,
   diferente. Se eu rodar via `16ca9ac1fa0f:*`, estou usando versão que NINGUÉM
   mais tem. Resultados ficam fragmentados. Já com `afiliados-skills:*`, ambos
   rodamos a mesma SKILL.md (latest publicada no GitHub do marketplace).

   **Anti-exemplo (24/05/2026)**: user invocou `/16ca9ac1fa0f:biblia-preencher`,
   Claude leu a SKILL.md inline e executou os passos manualmente em vez de
   chamar `Skill(skill="afiliados-skills:biblia-preencher", ...)`. Resultado
   idêntico nesse caso (versões iguais) mas sem garantia futura. Regra reforçada.

   **⚠️ Frescor da skill — o repo `.claude/skills/` é a FONTE DA VERDADE, não o cache do plugin (canon 2026-07-23).** O cache do plugin (`afiliados-skills:*` / `{hash}:*`) só atualiza no `/plugin marketplace update` e fica stale após qualquer edição de skill; o repo vem no `git pull` e está sempre na última versão. Como Marcelo E Bárbara têm o repo inteiro, a cópia do repo vence. Regras:
   - **Quando trabalhando NO repo (Claude Code local/VPS), a skill canônica é `.claude/skills/{nome}/SKILL.md`.** Se houver qualquer dúvida de que o cache do plugin pode estar atrás do repo (ex.: logo após mexer numa skill, ou numa sessão que não deu `/plugin marketplace update`), **leia o arquivo do repo direto** (`Read .claude/skills/{nome}/SKILL.md` e siga) em vez de confiar no cache. Isso elimina a classe stale.
   - **Uma regra DENTRO da skill não resolve isso** (bootstrapping: uma cópia stale carrega uma regra stale). Por isso a regra mora aqui, na CLAUDE.md, que é lida fresca todo início de sessão.
   - **Versão = git.** Não há campo `version:` no frontmatter (um número manual também drifta); o `git log -- .claude/skills/{nome}/SKILL.md` é o versionamento real. Pra saber se o cache está atrás: comparar com o `git HEAD` do repo.
   - **Após um release ao marketplace**, rodar `/plugin marketplace update` (e avisar a Bárbara) pra alinhar o cache de quem invoca por nome fora do repo. Ver [[afiliados.armadilha.plugin-cache-stale-apos-release]].

   - **Bíblia** (gasta ~$0.10-0.15 no painel evitados):
     - Preencher: `Skill(skill="biblia-preencher", args="<URL do editor-v2 OU ASIN OU nome>")`
     - Auditar:   `Skill(skill="biblia-auditar", args="<URL do editor-v2 OU ASIN OU nome>")`
   - **Página individual de produto** (gasta ~$0.07-0.12 no painel evitados):
     - Criar:     `Skill(skill="pagina-produto-criar", args="<URL do editor-produto OU site/slug>")`
     - Auditar:   `Skill(skill="pagina-produto-auditar", args="<URL do editor-produto OU site/slug>")`
   - **Review de produto em artigo** (gasta ~$0.05-0.10 no painel evitados):
     - Criar:     `Skill(skill="artigo-review-criar", args="<URL do editor-artigo — detecta stubs vazios; OU site/slug-artigo ASIN direto>")`
   - **Auditoria cross-produto de artigo** (gasta ~$0.10-0.20 no painel evitados):
     - Auditar:   `Skill(skill="artigo-reviews-auditar", args="<URL do editor-artigo OU site/slug-artigo>")`
   - **Meta description do artigo** (gasta ~$0.005-0.01 no painel evitados):
     - Escrever:  `Skill(skill="artigo-meta-escrever", args="<URL do editor-artigo OU site/slug-artigo>")`
   - **Introdução do artigo** (gasta ~$0.04-0.06 no painel evitados):
     - Escrever:  `Skill(skill="artigo-intro-escrever", args="<URL do editor-artigo OU site/slug-artigo>")`
   - **Guia "Como escolher" do artigo** (gasta ~$0.06-0.10 no painel evitados):
     - Escrever:  `Skill(skill="artigo-guia-escrever", args="<URL do editor-artigo OU site/slug-artigo>")`
   - **Auditoria do artigo** (gasta ~$0.06-0.10 no painel evitados):
     - Auditar:   `Skill(skill="artigo-auditar", args="<URL do editor-artigo OU site/slug-artigo>")` — audit completo: 38 categorias editoriais + 4 checks estruturais + readyToLock. Imprime relatório inline no chat + salva .md (painel lê). Consolidada em 2026-05-24 (antes existiam 2 skills separadas, artigo-auditar puro + artigo-analise-final com structural+lock; separação era artificial e foi removida).
   - **Descrição de categoria** (gasta ~$0.01-0.03 no painel evitados):
     - Escrever:  `Skill(skill="categoria-descricao-escrever", args="<URL do editor-categoria OU site/categorySlug>")`
   - **Páginas institucionais editoriais /sobre/ + /author/** (por nicho; E-E-A-T):
     - Escrever:  `Skill(skill="preencher-institucionais", args="<slug do site OU URL do painel>")` — faz as DUAS editoriais numa execução, DISTINTAS (sem duplicação): /sobre/ = voz do site (Missão + Quem está por trás + Como avaliamos {nicho} + Independência + [YMYL saúde] + Fale conosco); /author/ = voz da pessoa em 1ª pessoa (Como eu trabalho + Como eu avalio {nicho} + Meu compromisso). Molde melhoromega3. Autor/critérios/e-mail do config+niche (nunca inventados); metodologia VAGA (sem alegar teste físico NEM expor pesquisa de mesa); disclosure Amazon + YMYL (saúde); anti-clone cross-persona (Eduardo ×9, Gustavo ×3); alinha config.author.bio; cria /author/ se faltar. No marketplace (afiliados-skills). NÃO cobre contato/termos/privacidade (template+config).
2. NUNCA improvisar curadoria/auditoria sem antes carregar a SKILL.md
   correspondente. Cada skill tem ~280 linhas com armadilhas documentadas
   (voz comprador, travessão, HTML allowlist, filtros editoriais, etc.) —
   improvisar = cair em armadilhas que a skill já me alertaria.
3. Args informais (user diz "preenche a L3250 no melhorimpressora") → eu
   mapeio pra args canônico (`melhorimpressora/epson-ecotank-l3250`) antes
   de invocar. Se ambíguo, pergunto.
4. Fallback se Skill tool retornar "Unknown skill" (raríssimo): `Read .claude/skills/{nome}/SKILL.md`
   e seguir manualmente.

**Pré-requisitos no painel**:
- Bíblia: criada + dados brutos preenchidos no editor-v2 + imagem baixada
- Página individual: stub criado via "+ Nova página de produto" no site detail
  (endpoint `POST /product/:site/_actions/create-from-bible` cria `.mdx` +
  copia imagem). Só DEPOIS pedir aqui pra preencher conteúdo editorial.
- Artigo: stub criado via "✦ Criar artigo" no site detail (endpoint
  `POST /agent/site/:site/make-reviews-stub` cria esqueleto sem IA). Pode
  adicionar produtos depois via "+ Adicionar produto" no editor-artigo
  (`POST /agent/article/:site/:slug/add-products-stub`). Só DEPOIS pedir
  aqui pra preencher review per-produto.

**Por que esse fluxo existe**: Marcelo decidiu (2026-05-16) rodar IA
editorial via Claude Code aqui no chat em vez dos botões "✦ Preencher"
/ "✦ Auditar" / "✦ Criar com IA" do painel. Economiza `ANTHROPIC_API_KEY`
do painel e mantém paridade com prompts canônicos
(`docs/painel/_data/agent-prompts.json`) — skill + prompt JSON derivam
da mesma fonte editorial.

Ver memória `~/.claude/projects/-Users-marcelo-Documents-Claude/memory/afiliados.fluxo.preencher-auditar-via-claude-code.md`
pra contexto completo.

