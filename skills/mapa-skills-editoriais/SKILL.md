---
name: mapa-skills-editoriais
description: Índice COMPLETO das 24 skills do marketplace afiliados-skills — qual usar para cada objeto (bíblia, página de produto, artigo e suas partes, categoria, institucionais, linkagem, clone, lineup, migração, leilão), com pré-requisitos de painel e forma de invocação. Invoque quando estiver em dúvida sobre QUAL skill chamar. Não substitui as skills em si — é o índice delas.
---

# Mapa das skills editoriais

**Regra nº 1:** quando o pedido casa com uma skill, SEMPRE invocar a Skill tool
antes de qualquer outra ação — **inclusive quando o user usa slash-command**
(o SKILL.md carrega inline e há tentação de executar manualmente; não execute).
Regra nº 2: NUNCA improvisar curadoria/auditoria sem carregar a SKILL.md —
cada uma tem centenas de linhas de armadilhas documentadas.

**Namespace:** `Skill(skill="afiliados-skills:<nome>", args="...")` — nunca o
namespace `{hash}:*` (cache pinned de uma máquina; fragmenta versão entre
Marcelo e Bárbara). **Frescor:** trabalhando NO repo, a fonte da verdade é
`.claude/skills/{nome}/SKILL.md` (regra completa no CLAUDE.md, seção
"IA editorial"). Fallback pra "Unknown skill": `Read` do arquivo do repo.

Args: todas aceitam URL do painel OU args canônicos. User falou informal
("preenche a L3250 no melhorimpressora") → mapear pro canônico antes; ambíguo → perguntar.

## Bíblia v2

| Skill | Quando |
|---|---|
| `biblia-preencher` | curar os 7 campos editoriais de UMA bíblia (aceita `--enriquecer` = backfill sem sobrescrever) |
| `biblia-preencher-em-massa` | idem pra VÁRIAS em paralelo (≤10 sub-agents isolados); botão roxo "✨" do produtos.html |
| `biblia-auditar` | auditar+corrigir UMA (propor→aprovar; carimba lastAuditedAt + push R2 sempre) |
| `biblia-auditar-em-massa` | idem pra VÁRIAS, isoladas, auto-fix de direção conhecida; 2ª etapa do `--audit` ou sozinha |

Pré-requisito: bíblia criada + dados brutos + imagem no editor-v2.

## Página individual de produto

| Skill | Quando |
|---|---|
| `pagina-produto-criar` | preencher os 6 campos de UM stub |
| `pagina-produto-criar-em-massa` | todos os stubs vazios de um site (ou subset por ASIN), paralelo; flag `--audit` |
| `pagina-produto-auditar` | audit read-only de UMA página (21 categorias, cruza com bíblia) |

Pré-requisito: stub criado via "+ Nova página de produto" no site detail.

## Artigo comparativo — partes

| Skill | Quando |
|---|---|
| `artigo-lineup-montar` | escolher QUAIS produtos entram, ordem e papel (`--aplicar` cria o artigo no painel) |
| `artigo-review-criar` | review de UM produto no artigo (6 campos) |
| `artigo-intro-escrever` | intro (body markdown) + conserta title fora do padrão |
| `artigo-guia-escrever` | guideContent (5 H2 + extras SERP) — EXIGE concorrentes da keyword EXATA |
| `artigo-meta-escrever` | meta description (última coisa do artigo) |

Pré-requisito: stub via "✦ Criar artigo" / produtos via "+ Adicionar produto".
Ordem típica: lineup → reviews → guia → intro → meta → audits.

## Artigo comparativo — auditorias

| Skill | Quando |
|---|---|
| `artigo-reviews-auditar` | TODOS os reviews como conjunto (23 critérios cross-produto; normaliza subtitle/badge) — a cada 3 produtos ou antes de travar |
| `artigo-guia-auditar` | só o guideContent, correção cirúrgica por seção + faq-shuffle |
| `artigo-auditar` | artigo INTEIRO read-only (38 categorias + estruturais + readyToLock) — gate final antes de `contentLocked` |

## Escala / rede

| Skill | Quando |
|---|---|
| `artigo-clonar-em-massa` | clonar um artigo pra site irmão, conteúdo 100% novo das bíblias (full-auto, não deploya, não trava) |
| `artigo-clonar-fila` | N clones em sequência (lista do botão "▶ Copiar fila" do painel) |
| `linkagem-auditar` | linkagem interna do SITE inteiro (propor→aprovar; 2-4 peers/artigo, hub isento) |
| `categoria-descricao-escrever` | descrição de UMA categoria (`/categoria/{slug}/`) |
| `categoria-descricao-criar-em-massa` | várias categorias, agrupadas por categorySlug cross-site (anti-duplicata entre irmãs) |
| `preencher-institucionais` | /sobre/ + /author/ de um site, distintas, E-E-A-T (não cobre contato/termos/privacidade) |

## Operação / infra editorial

| Skill | Quando |
|---|---|
| `site-migrar-dominio` | migrar site de domínio com 301 catch-all (5 fases com gate; não registra domínio nem aponta NS) |
| `leilao-garimpar` | analisar a lista mensal de liberação do Registro.br (read-only; registro é decisão do Marcelo) |

Skills locais do repo (fora do marketplace): `backup-monorepo`,
`painel-launchagent`, `site-criar-workflow` — procedimento de máquina, não editorial.

## Por que via Skill tool e não os botões do painel

Decisão Marcelo 2026-05-16: IA editorial roda no Claude Code (assinatura) em
vez dos botões "✦" do painel (API key). Economiza a `ANTHROPIC_API_KEY` e
mantém paridade com os prompts canônicos (`docs/painel/_data/agent-prompts.json`).
Modelo: **Opus 5 (ou o Opus mais novo disponível) — NUNCA Sonnet/Haiku.**
Contexto completo: memória `afiliados.fluxo.preencher-auditar-via-claude-code.md`.
