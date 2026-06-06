---
name: linkagem-auditar
description: Audita E MELHORA a linkagem interna do SITE INTEIRO (cross-artigo), no estilo propor→aprovar (igual artigo-guia-auditar). Roda os núcleos determinísticos (scripts/audit-linkagem.ts = régua SEO + scripts/audit-links.ts = validade) + a camada de julgamento LLM (placement genuinamente contextual + oportunidades de links NOVOS naturais). Propõe os fixes, você aprova granular, e a skill aplica via Edit cirúrgico nos guideContent. Escopo: CONSERTAR (link-quebrado 404, link-home-errado /{homeReviewSlug}/→/, anchor-nao-keyword, anchor-produto-sem-nome, peer/home na Conclusão) + ADICIONAR links novos contextuais. NÃO faz hub-and-spoke. Aceita `site` OU URL do painel (linkagem-{site}.html). Fecho: commit --no-verify + push + painel-vps-pull (regenera linkagem-{site}.html = sincroniza no painel) + marcador `.audits/linkagem/{site}-last.md` (commit `audit-linkagem(...)`).
---

## Parse de input

Aceita 2 formatos no $ARGUMENTS:

**A) URL do painel** (forma preferida — botão roxo "📋 Copiar skill" da página linkagem):
- `https://painel.melhorserum.com.br/linkagem-melhorimpressora.html`
- Extrai `site` via regex `linkagem-([a-z0-9-]+)\.html`

**B) Slug do site direto**:
- `melhorimpressora`

Detecção: começa com `https://` → caminho A. Senão → caminho B (valida `[a-z0-9-]+`).

# Auditar e melhorar a linkagem interna do site inteiro (propor → aprovar)

Você é o auditor-editor da **linkagem interna do site todo**. Diferente das skills por-artigo (`artigo-auditar`, `artigo-guia-auditar`), esta enxerga o **grafo cross-artigo** (quem linka quem, balanço, órfãos), roda a régua determinística em todos os artigos de uma vez, e **aplica fixes no estilo propor→aprovar** — igual `artigo-guia-auditar` faz pro guide de um artigo, mas aqui pro grafo do site inteiro.

## Divisão de trabalho (NÃO reimplementar o que os scripts já fazem)

| Camada | Quem faz | Esta skill |
|---|---|---|
| Régua SEO determinística (grafo, âncora, slug, Conclusão, home-errado, hub-and-spoke) | `scripts/audit-linkagem.ts --json` | **roda e lê** |
| Validade (tag Amazon, linkCode, 404 interno, redirect externo) | `scripts/audit-links.ts --json` | **roda e lê** |
| Julgamento: placement *genuinamente* contextual? links NOVOS naturais? | **só LLM** | **agrega valor + propõe** |
| Aplicar os fixes aprovados (Edit cirúrgico no guideContent) | **a skill** | **aplica on-approval** |

Não reescreva extração de link nem grafo — os scripts já fazem. O valor da skill é (1) **consolidar** as duas saídas, (2) a **camada de julgamento** (placement + oportunidades), e (3) **aplicar** o que o user aprovar.

## Pré-requisitos

- Site existe em `sites/{site}/` com `src/content/reviews/*.mdx`.
- `scripts/audit-linkagem.ts` e `scripts/audit-links.ts` existem (núcleo determinístico).
- `bun` no PATH.
- Artigos a editar NÃO travados (`contentLocked: true` → pular esse artigo e avisar; nunca editar travado sem destrave explícito).

## Invariantes

- **PROPOR → APROVAR.** NUNCA aplica sem aprovação granular do user ("aplica tudo" / "aplica 1,3" / "aplica canon"). Antes de aplicar, imprime os diffs.
- **EDIÇÃO CIRÚRGICA, nunca rewrite.** Só toca no trecho do `guideContent` com o fix aprovado (um `<a>`/`<p>` por vez). Resto do `.mdx` byte-a-byte intacto. Preserva o block scalar `|` (NUNCA parseYaml/stringify do frontmatter — sempre `Edit` no trecho-alvo).
- **NÃO inventa.** Findings determinísticos vêm dos scripts (verbatim). Os de julgamento (placement/oportunidade) citam o trecho real do guideContent. Link novo só com âncora = keyword real do destino + href = slug REAL (nunca derivado do keyword).
- **Escopo fechado.** CONSERTAR (404/home-errado/âncora/slug/Conclusão) + ADICIONAR links novos contextuais. **NÃO faz hub-and-spoke** (linkar produto órfão é decisão editorial à parte). **NÃO mexe em tag Amazon** (isso é `scripts/fill-affiliate-tag.ts`).
- **Régua de linkagem canônica** (igual artigo-guia-escrever/auditar): âncora de peer = keyword do destino (singular preferido); âncora de produto = nome completo COM marca; href = slug REAL; peer/home links contextuais e NUNCA na Conclusão (produto/Amazon na Conclusão = OK); ≥2 peers distintos de saída; home linkada via `href="/"` (nunca `/{homeReviewSlug}/`).
- **Sem travessão.** Português brasileiro editorial.

## Fluxo

1. **Parse args**: detecta URL vs slug, extrai `site`. Valida `[a-z0-9-]+`.

2. **Git pull antes de ler** (evita estado stale — o painel VPS commita writes):
   ```bash
   git stash push -m "skill-linkagem-auditar-temp" 2>/dev/null
   git pull --rebase origin main 2>&1 | tail -3
   git stash pop 2>/dev/null
   ```

3. **Rodar a régua SEO determinística**:
   ```bash
   bun scripts/audit-linkagem.ts {site} --json
   ```
   Parse: `{ counts, findings:[{level,type,article,message}], homeReviewSlug, affiliateTag, totalArticles }`.

4. **Rodar a validade de links** (estrutural por padrão; só Amazon/internos, sem fetch):
   ```bash
   bun scripts/audit-links.ts {site} --no-fetch --json
   ```
   Use SÓ pra contexto (tag/404 interno). **Não conserte tag aqui** — só reporte que `fill-affiliate-tag.ts` resolve.

5. **Camada de julgamento LLM** (o valor que script não dá). Read os `.mdx` dos artigos com links peer/home + os com FAQ/seções relevantes. Avalie:
   - **Placement genuinamente contextual?** Para cada link peer/home existente, o parágrafo onde ele está fala MESMO do tema do destino? "Fora da Conclusão" é necessário mas não suficiente. Sinalize os fracos com spot melhor.
   - **Oportunidades de links NOVOS.** Há FAQ/H3/seção que toca no tema de um peer ainda não-linkado (ou pouco-linkado), onde um link cairia natural? Liste só as genuinamente naturais — NUNCA force link decorativo. Para cada: artigo origem, peer destino, **spot exato** (cite a frase âncora), **âncora sugerida** (= keyword singular do destino), e o **Edit proposto** (frase antes → depois).
   - **Balanço do grafo.** Algum artigo órfão/sublinkado/hub-demais? Sugira 1-2 links que equilibram (respeitando contextualidade).

6. **Montar o relatório de propostas** (formato abaixo) com TODOS os fixes numerados (consertos + links novos), cada um com o diff `ANTES → DEPOIS`. **Imprime inline. NÃO aplica nada ainda.**

7. **Gravar o marcador de auditoria** (registra QUANDO auditou — roda SEMPRE, logo após o relatório, mesmo que o user rejeite tudo depois; auditar é o evento):
   ```bash
   mkdir -p docs/biblias-v2/.audits/linkagem
   ```
   `Write` em `docs/biblias-v2/.audits/linkagem/{site}-last.md`: título (`# Auditoria de linkagem: {site}`), contagens (`- Erros: N · Avisos: M · Infos: K · Oportunidades: O`), lista curta dos tipos disparados (ou "nenhum"). **NÃO** invente timestamp (a fonte de tempo é o commit git).

8. **Esperar aprovação granular.** "aplica tudo" / "aplica 1,3" / "aplica canon" (por tema) / "rejeita 2" / "refaz 1".

9. **Backup** antes de aplicar (1 por artigo tocado):
   `docs/painel/.painel-backups/{YYYY-MM-DD}/article-{site}-{slug}-{HHMMSS}-guide.mdx` (via helper `readGuideContent` do painel, mesmo formato dos outros).

10. **Aplicar os aprovados** via `Edit` cirúrgico no `guideContent` do `.mdx` (preservar indent 2 espaços do block scalar; um trecho por vez). Regras:
    - **anchor-nao-keyword**: trocar SÓ o texto entre `<a>...</a>` pela keyword (qualificadores ficam FORA do `<a>`).
    - **anchor-produto-sem-nome**: trocar o texto pelo nome completo do produto (com marca).
    - **link-home-errado**: trocar `href="/{homeReviewSlug}/"` por `href="/"` (manter a âncora = keyword da home).
    - **link-quebrado**: corrigir o href pro slug REAL (confirmar o arquivo existe) OU, se não há destino, remover o `<a>` mantendo o texto.
    - **peer-link-na-conclusao**: MOVER o link pro spot contextual aprovado (remover da Conclusão + inserir no parágrafo-alvo). Produto/Amazon na Conclusão ficam.
    - **link novo**: inserir o `<a>` no spot exato aprovado, âncora = keyword singular do destino, href = slug REAL (`/slug/` ou `/` pra home), sem `rel`/`target` (interno passa autoridade).

11. **Build** (gate): `pnpm --filter {site} build`. Se Zod/Astro falhar, reverter do backup e reportar.

12. **Re-rodar `bun scripts/audit-linkagem.ts {site}`** pós-fix pra confirmar que os findings aprovados sumiram e nada regrediu (≥2 peers, 0 na Conclusão, 0 broken/home-errado).

13. **Git add + commit (`--no-verify`) + push + VPS pull**:
    ```bash
    git add sites/{site}/src/content/reviews/{slugs-tocados}.mdx
    git add docs/biblias-v2/.audits/linkagem/{site}-last.md
    git commit --no-verify -m "fix({site}): linkagem interna via skill (N consertos + M links novos)"
    git push origin main
    bash scripts/painel-vps-pull.sh
    ```
    `--no-verify` necessário (hook Fase J bloqueia `reviews/*.mdx`). **O `painel-vps-pull.sh` dispara `/admin/update`, que roda `gen.ts` full → regenera `linkagem-{site}.html` = o painel mostra o resultado final ("sincroniza lá").**

14. **Reportar** o resultado: o que foi aplicado, o grafo pós-fix, o path do backup, e o link da página de linkagem no painel.

## Formato do relatório de propostas

```markdown
# Linkagem: {site}

**{N} artigos · tag: {affiliateTag} · home: {homeReviewSlug ou "grid"}**
**Determinístico:** {errors} erros · {warnings} avisos · {infos} infos

## 🔴 Consertos propostos
### 1. [{type}] {article} `{slug}`
- **Problema**: {message do script}
- **Fix** (cirúrgico):
  ```
  ANTES:  <p>... <a href="/x/">y</a> ...</p>
  DEPOIS: <p>... <a href="/x/">{keyword}</a> ...</p>
  ```

## 💡 Links novos propostos
### N. {article} → {peer} (na {seção/FAQ "..."})
- **Por quê natural**: {1 frase}
- **Fix**:
  ```
  ANTES:  <p>...frase-alvo.</p>
  DEPOIS: <p>...frase-alvo. {nova frase com <a href="/peer/">keyword</a>}.</p>
  ```

## Como aplicar
- **"aplica tudo"** · **"aplica 1,3"** (por número) · **"aplica consertos"** (só os 🔴) · **"rejeita 2"** · **"refaz 1"**
```

## Critérios (referência — vêm dos scripts)

- `link-quebrado` (error), `link-home-errado` (error), `slug-vs-keyword` (warn), `linkagem-fraca` (warn, <2 peers distintos de saída), `peer-repetido` (warn), `anchor-nao-keyword` (warn), `anchor-produto-sem-nome` (warn), `peer-link-na-conclusao` (info), `hub-and-spoke-incompleto` (info — **fora de escopo desta skill**), `orfao`/`sublinkado`.

## Armadilhas

1. **Reimplementar grafo/extração.** Os scripts já fazem — rode e leia o JSON.
2. **Rewrite do guide.** É cirúrgico por trecho; nunca reescreva o guide inteiro (isso é `artigo-guia-escrever`).
3. **parseYaml/stringify no frontmatter.** Bagunça o block scalar `|`. Sempre `Edit` no trecho.
4. **Forçar link novo decorativo.** Só proponha se o spot REALMENTE toca no tema do destino. Melhor 0 honestas que 5 forçadas.
5. **Aplicar sem aprovar.** Esta skill é propor→aprovar. Imprime os diffs e espera.
6. **Esquecer `--no-verify`.** O hook Fase J bloqueia `reviews/*.mdx`.
7. **Editar artigo travado.** `contentLocked: true` → pular + avisar.
8. **Achar que o painel não atualiza.** Atualiza: `/admin/update` roda `gen.ts` full → `linkagem-{site}.html` regenera. Não precisa de passo extra.

## Invocação

```
audita e melhora a linkagem do melhorimpressora
/linkagem-auditar impressoraideal
```

Args canônico: `Skill(skill="afiliados-skills:linkagem-auditar", args="melhorimpressora")`.

## Sincronização painel ↔ skill

A skill grava `.audits/linkagem/{site}-last.md` (1º marcador por-SITE; os outros audits são por-artigo/ASIN). A página `linkagem-{site}.html` (gerada por `gen.ts:linkagemContent`) reflete o grafo pós-fix automaticamente no `painel-vps-pull` (gen full). O botão roxo "📋 Copiar skill" dessa página copia `/linkagem-auditar {site}` pro clipboard. A pill "Linkagem auditada" no site-detail é follow-up (`/activity` lê o commit `audit-linkagem(`).
