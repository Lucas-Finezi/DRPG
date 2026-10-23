# DRPG — Base de regras (extração do SRD 5.2.1)

Este repositório converte documentos de sistemas de RPG com licença aberta em JSON
estruturado e rastreável para o motor de regras do Discovery RPG. O primeiro sistema é
o **D&D SRD 5.2.1** (CC-BY-4.0).

**Regra central:** todo conteúdo vem exclusivamente de `source/SRD_CC_v5.2.1.pdf`.
- Nada é inventado, completado com conhecimento externo ou simplificado.
- Divergências internas da própria fonte são registradas, e não corrigidas.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `source/` | PDF original (imutável) e seu SHA-256 |
| `extraction/` | Texto extraído e validado (bruto por página e Markdown estruturado); ver `extraction/README.md` |
| `inventory/dnd5e/srd-5.2.1/` | **L00**: inventário da fonte (capítulos, seções, tabelas, entradas esperadas, plano de lotes) |
| `tools/` | Scripts reprodutíveis de extração e inventário |

## Ordem de leitura para agentes

1. Este README.
2. `extraction/README.md`: como o texto foi obtido e validado.
3. `inventory/dnd5e/srd-5.2.1/README.md` e `lots.json`: o que existe na fonte e qual lote cuida de quê.
4. `inventory/dnd5e/srd-5.2.1/entries.json`: a lista de entradas esperadas, com `ref`, página e lote.
5. `extraction/SRD_CC_v5.2.1.md`: o texto da fonte, consultado pelos marcadores `<!-- page N -->`.

## Como gerar de novo

```bash
pip install -r tools/extract/requirements.txt          # e poppler-utils (pdftotext)
python3 -I tools/extract/extract_srd.py source/SRD_CC_v5.2.1.pdf extraction
python3 -I tools/inventory/build_inventory.py
```

## Status dos lotes

| Fase | Lotes | Status |
|---|---|---|
| 0 — Fundações | L00 Inventário da fonte | concluído |
| 0 — Fundações | L01 Contrato base, L02 Sistema D&D 5e | pendente |
| 1 — Regras compartilhadas | L03–L09 | pendente |
| 2 — Catálogos de personagem | L10–L16 | pendente |
| 3 — Magias | L17–L27 | pendente |
| 4 — Equipamentos e itens | L28–L32 | pendente |
| 5 — Criaturas e encontros | L33–L42 | pendente |
| 6 — Integração e auditoria | L43–L46 | pendente |

## Licença do conteúdo

This work includes material from the System Reference Document 5.2.1 ("SRD 5.2.1") by
Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is
licensed under the Creative Commons Attribution 4.0 International License, available at
https://creativecommons.org/licenses/by/4.0/legalcode.
