# afiliados-skills

Skills editoriais do **ProjetoAfiliados** (sites de review/afiliados Amazon Brasil) empacotadas como Claude Code plugin. Substitui os botões de IA do painel — roda localmente via Claude Code do colaborador em vez de gastar `ANTHROPIC_API_KEY` da VPS.

## Skills incluídas

| Skill | O que faz |
|---|---|
| `biblia-preencher` | Preenche os 7 campos de curadoria da bíblia v2 (`docs/biblias-v2/<ASIN>.json`) a partir dos dados brutos |
| `biblia-auditar` | Audita bíblia v2 em categorias e gera relatório em `.audits/` |
| `pagina-produto-criar` | Preenche os 6 campos editoriais da página individual (`sites/<site>/src/content/products/<slug>.mdx`) |
| `pagina-produto-criar-em-massa` | Cria várias páginas individuais em paralelo (sub-agents), 1 commit lote; flag opcional `--audit` |
| `pagina-produto-auditar` | Audita página individual; inclui categoria cross-site (`compare-cross-site.py` — duplicata de prosa entre sites irmãos) |
| `artigo-review-criar` | Preenche o review de 1 produto dentro de um artigo comparativo (+ campos top-level se o artigo for stub) |
| `artigo-reviews-auditar` | Auditoria CROSS-PRODUTO dos reviews — analisa todos juntos (tone-clone, redundância, claim-vs-lineup, links, voz-comprador) e corrige por aprovação granular |
| `artigo-meta-escrever` | Escreve a meta description SEO do artigo |
| `artigo-intro-escrever` | Escreve a introdução (body markdown) do artigo |
| `artigo-guia-escrever` | Gera/reescreve o `guideContent` inteiro (Vale a pena / Como escolher / Marcas / FAQ / Conclusão) |
| `artigo-guia-auditar` | Audita o `guideContent` e corrige CIRÚRGICO por seção (sem rewrite) — contraparte do `artigo-reviews-auditar` pro guia. Pega produto do lineup fora do guia, link interno quebrado, estrutura, etc. |
| `artigo-auditar` | Auditoria read-only do artigo inteiro (categorias editoriais + checks estruturais + `readyToLock`) |
| `categoria-descricao-escrever` | Escreve a descrição de uma categoria do site |
| `artigo-clonar-em-massa` | Clona um artigo pra outro site (assembler determinístico + auditorias por etapa) |

## Instalação

No Claude Code:

```
/plugin marketplace add marcelohaz/afiliados-skills
/plugin install afiliados-skills@afiliados-skills
```

Ou, se já tem o repo clonado localmente:

```
/plugin marketplace add /caminho/pra/afiliados-skills
/plugin install afiliados-skills@afiliados-skills
```

Depois reinicia o Claude Code (Cmd+Q + abrir). As 14 skills viram disponíveis no `/`.

Pra atualizar quando sair release nova:

```
/plugin marketplace update afiliados-skills
/plugin update afiliados-skills@afiliados-skills
```

## Pré-requisitos

Skills assumem que você está rodando do diretório raiz do ProjetoAfiliados:

```bash
cd ~/Documents/Claude/Projects/ProjetoAfiliados
```

E que tem:
- `.env.painel-skills` configurado com credenciais do painel (pra disparar VPS pull)
- Auth do git configurada (Personal Access Token ou SSH key) — skills fazem push automático
- Permissão pra rodar `bun scripts/painel-vps-pull.sh`

Documentação completa em `docs/skills/README.md` do ProjetoAfiliados.

## Sincronização com prompts canônicos

Cada SKILL.md é versão executável local dos prompts canônicos em `docs/painel/_data/agent-prompts.json` do ProjetoAfiliados:

| Skill | Prompt canônico |
|---|---|
| `biblia-preencher` | `ops.curate_bible` |
| `biblia-auditar` | `ops.audit_bible` |
| `pagina-produto-criar` | `ops.create_product_page` |
| `pagina-produto-criar-em-massa` | local-only (espelha `create_product_page` por produto, via sub-agents) |
| `pagina-produto-auditar` | `ops.audit_product_page` |
| `artigo-review-criar` | `ops.rewrite_product` + `ops.make_reviews` (top-level) |
| `artigo-reviews-auditar` | `ops.improve_reviews` |
| `artigo-meta-escrever` | `ops.rewrite_meta_description` |
| `artigo-intro-escrever` | `ops.generate_intro` |
| `artigo-guia-escrever` | `ops.generate_guide` |
| `artigo-guia-auditar` | `ops.improve_guide` |
| `artigo-auditar` | `ops.audit_article` (+ structural/readyToLock) |
| `categoria-descricao-escrever` | `ops.category_description` |
| `artigo-clonar-em-massa` | local-only (sem op canônico) |

Em caso de divergência, o prompt canônico ganha. Quando Marcelo edita regras editoriais via `agent-config.html` do painel, esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Licença

MIT
