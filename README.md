# afiliados-skills

Skills editoriais do **ProjetoAfiliados** (sites de review/afiliados Amazon Brasil) empacotadas como Claude Code plugin. Substitui os botões de IA do painel — roda localmente via Claude Code do colaborador em vez de gastar `ANTHROPIC_API_KEY` da VPS.

## Skills incluídas

| Skill | O que faz |
|---|---|
| `preencher-biblia` | Preenche os 7 campos da bíblia v2 (`docs/biblias-v2/<ASIN>.json`) a partir dos dados brutos |
| `auditar-biblia` | Audita bíblia v2 em 5 categorias e gera relatório em `.audits/` |
| `preencher-pagina-produto` | Preenche os 6 campos editoriais da página individual (`sites/<site>/src/content/products/<slug>.mdx`) |
| `auditar-pagina-produto` | Audita página individual em 9 categorias e gera relatório em `.audits/products/` |
| `preencher-produto-em-artigo` | Preenche o review de 1 produto dentro de um artigo comparativo |
| `auditar-reviews-em-artigo` | Auditoria CROSS-PRODUTO — analisa todos os reviews do artigo juntos, detecta tone-clone, redundância, comparações factualmente erradas |

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

Depois reinicia o Claude Code (Cmd+Q + abrir). As 6 skills viram disponíveis no `/`.

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
| `preencher-biblia` | `ops.curate_bible` |
| `auditar-biblia` | `ops.audit_bible` |
| `preencher-pagina-produto` | `ops.create_product_page` |
| `auditar-pagina-produto` | `ops.audit_product_page` |
| `preencher-produto-em-artigo` | `ops.rewrite_product` + `ops.make_reviews` (top-level) |
| `auditar-reviews-em-artigo` | `ops.improve_reviews` |

Em caso de divergência, o prompt canônico ganha. Quando Marcelo edita regras editoriais via `agent-config.html` do painel, esta SKILL.md pode ficar atrasada — atualizar manualmente quando notar drift.

## Licença

MIT
