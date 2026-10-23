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
| `schema/` | **L01**: contrato de dados (JSON Schemas + exemplos válidos); ver `schema/README.md` |
| `knowledge/dnd5e/system.json` | **L02**: definição do sistema e registros que fecham o vocabulário de efeitos |
| `knowledge/dnd5e/entries/<kind>/<slug>.json` | Entradas de catálogo, uma por arquivo |
| `tools/` | Scripts reprodutíveis: `extract/`, `inventory/`, `build/` (um construtor por lote), `validate/` |
| `docs/decisions.md` | Decisões do projeto (D-001 acesso de classe às magias pelo cabeçalho; D-002 idioma) |

## Ordem de leitura para agentes

1. Este README.
2. `extraction/README.md`: como o texto foi obtido e validado.
3. `schema/README.md` e `schema/*.schema.json`: o formato dos dados e o vocabulário de `op`.
4. `knowledge/dnd5e/system.json`: o sistema e seus registros.
5. `inventory/dnd5e/srd-5.2.1/README.md` e `lots.json`: o que existe na fonte e qual lote cuida de quê.
6. `inventory/dnd5e/srd-5.2.1/entries.json`: a lista de entradas esperadas, com `ref`, página e lote.
7. `extraction/SRD_CC_v5.2.1.md`: o texto da fonte, consultado pelos marcadores `<!-- page N -->`.

## Como gerar de novo

```bash
pip install -r tools/requirements.txt                  # e poppler-utils (pdftotext)
python3 -I tools/extract/extract_srd.py source/SRD_CC_v5.2.1.pdf extraction   # texto
python3 -I tools/build/run_all.py          # inventário, todos os lotes em ordem e todas as checagens
```

`run_all.py` executa:
- **construção:** `build_inventory.py` (L00) e os construtores `tools/build/lNN_*.py` em ordem; `l01_examples.py` por último;
- **checagens:**
  - `validate.py`: schemas, exemplos, sistema e entradas;
  - `selftest.py`: o validador rejeita erros conhecidos;
  - `coverage.py`: cada trecho da fonte está em alguma entrada do seu lote;
  - `refs.py`: todo `ref` existe ou está previsto para um lote futuro, e toda entrada esperada de um lote já construído existe.

## Status dos lotes

| Fase | Lotes | Status |
|---|---|---|
| 0 — Fundações | L00 Inventário da fonte | concluído |
| 0 — Fundações | L01 Contrato base | concluído |
| 0 — Fundações | L02 Sistema D&D 5e | concluído (system.json + 43 entradas de regra; cobertura 436/436 trechos) |
| 1 — Regras compartilhadas | L03 Condições | concluído (15 condições + regra; 84/84 trechos) |
| 1 — Regras compartilhadas | L04 Regras de combate | concluído (12 ações, 32 termos, seções e quadros; 304/304) |
| 1 — Regras compartilhadas | L05 Testes e proficiências | concluído (16 termos, 3 atitudes, seções; 201/201) |
| 1 — Regras compartilhadas | L06 Dano, cura e resistências | concluído (20 termos, 5 perigos, seções; 137/137) |
| 1 — Regras compartilhadas | L07 Recursos e descansos | concluído (descansos, Dados de Vida; 31/31) |
| 1 — Regras compartilhadas | L08 Regras de equipamento | concluído (CA, treino em armadura, carga, moedas, criação; 43/43) |
| 1 — Regras compartilhadas | L09 Regras de magia | concluído (espaços, componentes, concentração, áreas; 145/145) |
| 2 — Catálogos de personagem | L10 Espécies | concluído (9 espécies + seções; 129/129) |
| 2 — Catálogos de personagem | L11 Antecedentes | concluído (4 antecedentes + seções; 61/61) |
| 2 — Catálogos de personagem | L12 Classes | concluído (12 classes com tabelas de progressão; 234/234) |
| 2 — Catálogos de personagem | L13 Subclasses | concluído (12 subclasses; 42/42) |
| 2 — Catálogos de personagem | L14 Features | concluído (303 features: 33 traços de espécie, 232 de classe/subclasse, 10 Metamagias, 28 Invocações; 1220/1220) |
| 2 — Catálogos de personagem | L15 Talentos | concluído (17 talentos + seções e quadro; 94/94) |
| 2 — Catálogos de personagem | L16 Multiclasse | concluído (regras e tabela Multiclass Spellcaster; 59/59) |
| 3 — Magias | L17 Truques | concluído (27 magias; 238/238) |
| 3 — Magias | L18 Magias de círculo 1 | concluído (57 magias; 472/472) |
| 3 — Magias | L19 Magias de círculo 2 | concluído (57 magias + Otherworldly Steed; 509/509) |
| 3 — Magias | L20 Magias de círculo 3 | concluído (42 magias; 378/378) |
| 3 — Magias | L21 Magias de círculo 4 | concluído (34 magias + Giant Insect; 331/331) |
| 3 — Magias | L22 Magias de círculo 5 | concluído (38 magias + Animated Object e Draconic Spirit; 437/437) |
| 3 — Magias | L23 Magias de círculo 6 | concluído (31 magias; 296/296) |
| 3 — Magias | L24 Magias de círculo 7 | concluído (20 magias; 235/235) |
| 3 — Magias | L25 Magias de círculo 8 | concluído (17 magias; 175/175) |
| 3 — Magias | L26 Magias de círculo 9 | concluído (16 magias; 174/174) |
| 3 — Magias | L27 Listas de magia | concluído (8 listas de classe + 8 de subclasse, 939 vínculos, divergências registradas; 1040/1040) |
| 4 — Equipamentos e itens | L28–L32 | pendente |
| 5 — Criaturas e encontros | L33–L42 | pendente |
| 6 — Integração e auditoria | L43–L46 | pendente |

## Licença do conteúdo

This work includes material from the System Reference Document 5.2.1 ("SRD 5.2.1") by
Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is
licensed under the Creative Commons Attribution 4.0 International License, available at
https://creativecommons.org/licenses/by/4.0/legalcode.
