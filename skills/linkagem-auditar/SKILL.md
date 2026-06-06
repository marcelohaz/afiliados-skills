---
name: linkagem-auditar
description: Audita a linkagem interna do SITE INTEIRO (read-only, cross-artigo) — junta a régua SEO determinística (scripts/audit-linkagem.ts) + a validade de links (scripts/audit-links.ts) + uma camada de julgamento LLM que só uma IA faz (se o link está num spot GENUINAMENTE contextual, não só "fora da Conclusão", e quais links NOVOS naturais dá pra adicionar). Aceita `site` OU URL do painel (linkagem-{site}.html). Checa: link quebrado / home-errado (/{homeReviewSlug}/ = 404), âncora=keyword (peer) / nome+marca (produto), ≥2 peers distintos de saída, peer/home na Conclusão, slug-vs-keyword, hub-and-spoke incompleto, tag Amazon (tag-aware). NÃO edita conteúdo (read-only) — sugere; os fixes vão por artigo-guia-auditar (âncora/posição) e scripts/fill-affiliate-tag.ts (tag). Grava marcador `.audits/linkagem/{site}-last.md` (commit `audit-linkagem(...)`).
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida):
- `https://painel.melhorserum.com.br/linkagem-melhorimpressora.html`
- Extrai `site` do nome do arquivo (`linkagem-{site}.html`)

**B) Slug do site direto**:
- `melhorimpressora`

Detecção: começa com `https://` → caminho A (regex `linkagem-([a-z0-9-]+)\.html`). Senão → caminho B (valida `[a-z0-9-]+`).

# Auditar a linkagem interna do site inteiro (read-only, cross-artigo)

Você é o auditor read-only da **linkagem interna do site todo**. Diferente das skills por-artigo (`artigo-auditar`, `artigo-guia-auditar`), esta enxerga o **grafo cross-artigo** (quem linka quem, balanço de entradas/saídas, órfãos) + roda a régua determinística em todos os artigos de uma vez + adiciona a camada que só LLM resolve.

A skill é **read-only no conteúdo**: NÃO toca `.mdx`. Só roda os scripts, sintetiza, imprime relatório e commita o `.md` do marcador.

## Divisão de trabalho (NÃO reimplementar o que os scripts já fazem)

| Camada | Quem faz | Esta skill |
|---|---|---|
| Régua SEO determinística (grafo, âncora, slug, Conclusão, hub-and-spoke, home-errado) | `scripts/audit-linkagem.ts --json` | **roda e lê** |
| Validade (tag Amazon, linkCode, 404 interno, redirect externo) | `scripts/audit-links.ts --json` | **roda e lê** |
| Julgamento: placement *genuinamente* contextual? oportunidades novas? | **só LLM** | **agrega valor aqui** |

Não reescreva extração de link nem grafo — os scripts já fazem. O valor da skill é (1) **consolidar** as duas saídas num relatório acionável e (2) a **camada de julgamento** que script nenhum dá.

## Pré-requisitos

- Site existe em `sites/{site}/` com `src/content/reviews/*.mdx`.
- `scripts/audit-linkagem.ts` e `scripts/audit-links.ts` existem (núcleo determinístico da Fase 1).
- `bun` no PATH.

## Invariantes

- **READ-ONLY no conteúdo.** Nunca edita `.mdx`. Só roda scripts + escreve/commita o marcador `.md`.
- **NÃO inventa findings.** Os findings determinísticos vêm dos scripts (verbatim). Os de julgamento (placement/oportunidade) precisam citar o trecho real do guideContent.
- **Fixes têm dono.** A skill SUGERE; quem aplica:
  - âncora errada / link na Conclusão / peer faltando → `artigo-guia-auditar` (cirúrgico por seção) ou edição manual.
  - tag Amazon ausente/errada → `scripts/fill-affiliate-tag.ts {site} --apply`.
  - link quebrado / home-errado → corrigir o `href` (slug real / `/` pra home).
- **Português brasileiro editorial.** Tom analítico.

## Fluxo

1. **Parse args**: detecta URL vs slug, extrai `site`. Valida `[a-z0-9-]+`.

2. **Git pull antes de ler** (evita estado stale — o painel VPS commita writes):
   ```bash
   git stash push -m "skill-linkagem-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```
   Se falhar (offline/conflito), segue mesmo assim.

3. **Rodar a régua SEO determinística**:
   ```bash
   bun scripts/audit-linkagem.ts {site} --json
   ```
   Parse o JSON: `{ counts:{errors,warnings,infos}, findings:[{level,type,article,message}], homeReviewSlug, affiliateTag, totalArticles }`.

4. **Rodar a validade de links** (sem fetch por padrão — rápido; com fetch só se o user pedir "checar 404 externos"):
   ```bash
   bun scripts/audit-links.ts {site} --no-fetch --json
   ```
   Parse: `{ counts:{errors,warnings}, issues:[{level,type,url,message,article,product}] }`.
   - Para checar 404/redirect reais (Amazon + externos via HTTP), rode SEM `--no-fetch` (mais lento). Mencione no relatório que foi modo estrutural se usou `--no-fetch`.

5. **Camada de julgamento LLM** (o valor que script não dá). Leia o `guideContent` dos artigos que têm links peer/home (frontmatter dos `.mdx`) e avalie:
   - **Placement genuinamente contextual?** Para cada link peer/home, o spot onde ele está fala MESMO do tema do destino, ou é decorativo (ex: jogado solto numa FAQ não-relacionada)? "Fora da Conclusão" é necessário mas não suficiente — julgue se o parágrafo realmente puxa o assunto do artigo-irmão. Sinalize os fracos com sugestão de spot melhor.
   - **Oportunidades NOVAS, naturais e contextuais.** Há FAQ/H3/seção que toca no tema de um peer ainda não-linkado, onde um link cairia natural? (ex: FAQ "X ou Y?" num artigo poderia linkar o guia de Y). Liste só as que são genuinamente naturais — NÃO force link decorativo. Diga o spot exato + âncora sugerida (= keyword singular do destino).
   - **Balanço do grafo.** Olhando entradas/saídas: algum artigo é hub demais / órfão / sublinkado de um jeito que vale rebalancear? Sugira 1-2 links que equilibram.

6. **Montar o relatório consolidado** (formato abaixo). Junta: erros determinísticos (scripts) + julgamento LLM + oportunidades.

7. **Gravar o marcador** (registra QUANDO a linkagem do site foi auditada — alimenta futura pill "Linkagem auditada" no painel). Roda SEMPRE, mesmo com 0 findings:
   - `Write` em `docs/biblias-v2/.audits/linkagem/{site}-last.md` com: título (`# Auditoria de linkagem: {site}`), contagens (`- Erros: N · Avisos: M · Infos: K · Oportunidades: O`), lista curta dos tipos disparados (ou "nenhum"). **NÃO** invente timestamp pra sort (a fonte de tempo é o commit git). Crie o diretório se não existir.
   - Commit + push + VPS pull:
     ```bash
     mkdir -p docs/biblias-v2/.audits/linkagem
     git add docs/biblias-v2/.audits/linkagem/{site}-last.md
     git commit --no-verify -m "audit-linkagem({site}): {N} erros, {M} avisos, {O} oportunidades"
     git push origin main
     bash scripts/painel-vps-pull.sh
     ```
   - **Por quê o nome `-last.md`** (sem dígitos de data): não cai no `.gitignore` de audits timestampados → fica tracked e sincroniza. O prefixo de commit `audit-linkagem(` é o marcador classificável (paridade com `audit-guia(`/`audit-reviews`).

8. **Imprimir o relatório COMPLETO inline no chat** (não só o summary). User vê tudo sem abrir arquivo. Path do `.md` no fim.

## Formato do relatório

```markdown
# Auditoria de linkagem: {site}

**{N} artigos · tag: {affiliateTag} · home: {homeReviewSlug ou "grid"}**
**Determinístico:** {errors} erros · {warnings} avisos · {infos} infos (régua) + {linkErrors} erros de validade (links)

## 🔴 Erros (corrigir antes do go-live)
- [{type}] {article}: {message}   ← dos scripts (link-quebrado, link-home-errado, tag Amazon errada)

## 🟡 Avisos
- [{type}] {article}: {message}   ← âncora≠keyword, slug-vs-keyword, ≥2 peers, peer-repetido

## 🔵 Infos
- [{type}] {article}: {message}   ← peer-na-conclusão, hub-and-spoke, sublinkado

## 🧠 Julgamento (placement)
- {article}: o link pra {peer} está em "{spot}" — {contextual ✅ / fraco ⚠ + spot melhor sugerido}

## 💡 Oportunidades (links novos naturais)
- {article} → {peer}: na {seção/FAQ "..."} cabe natural; âncora "{keyword singular}". Motivo: {1 frase}

## Como aplicar
- âncora/posição/peer faltando → `artigo-guia-auditar {site}/{slug}` (cirúrgico)
- tag Amazon → `bun scripts/fill-affiliate-tag.ts {site} --apply`
- link quebrado/home-errado → corrigir o href (slug real / `/` pra home)
```

Imprima inline. NÃO aplique nada (read-only).

## Critérios (referência — vêm dos scripts)

Determinísticos (não re-derivar; ler do JSON):
- `link-quebrado` (error) — href interno pra slug inexistente (404).
- `link-home-errado` (error) — `/{homeReviewSlug}/` em vez de `/` (filtrado do getStaticPaths → 404 em produção).
- `slug-vs-keyword` (warn) — slug ≠ slugify(keyword); ok se slug curto intencional, vira problema só se um link derivar o href do keyword.
- `linkagem-fraca` (warn) — < 2 peers DISTINTOS de saída (cap = nº de peers disponíveis no site).
- `peer-repetido` (warn) — mesmo peer linkado 2+ vezes do mesmo artigo.
- `anchor-nao-keyword` (warn) — âncora de peer ≠ keyword do destino (singular preferido; plural aceito).
- `anchor-produto-sem-nome` (warn) — âncora de produto ≠ nome completo (com marca).
- `peer-link-na-conclusao` (info) — navegação peer/home na Conclusão (decorativa; mover pra spot contextual). Produto/Amazon na Conclusão = OK.
- `hub-and-spoke-incompleto` (info) — página de produto existe mas não é linkada de nenhum guia.
- `orfao`/`sublinkado` (warn/info) — 0 / 1 fonte de links entrantes.
- Validade (audit-links): `affiliate-tag-missing` (tag ausente/errada), `internal-404`, `http-404`/redirect (com fetch).

## Armadilhas

1. **Reimplementar grafo/extração.** Os scripts já fazem — só rode e leia o JSON.
2. **Editar `.mdx`.** Esta skill é read-only; fixes vão pelas ferramentas com dono (acima).
3. **Forçar oportunidade decorativa.** Só sugira link novo se o spot REALMENTE toca no tema do destino. Melhor 0 sugestões honestas que 5 forçadas.
4. **Esquecer `--no-verify` no commit do marcador.** O hook Fase J bloqueia paths sensíveis; o marcador `.md` passa, mas use `--no-verify` por consistência com as outras skills de audit.
5. **Inventar timestamp no marcador.** A fonte de tempo é o commit git; `Date().toISOString()` cai em bug de timezone.

## Invocação

```
audita a linkagem do melhorimpressora
audita linkagem de https://painel.melhorserum.com.br/linkagem-impressoraideal.html
```

Args canônico: `Skill(skill="afiliados-skills:linkagem-auditar", args="melhorimpressora")`.

## Sincronização painel ↔ skill

A skill grava `.audits/linkagem/{site}-last.md` (1º marcador por-SITE; os outros audits são por-artigo/ASIN). A **pill "Linkagem auditada"** no site-detail é follow-up no painel (`/activity` + render) — espelhando como `audit-guia(`/`audit-reviews` viram pills. Enquanto a pill não existe, o marcador já fica tracked + sincronizado pra quando for ligada.
