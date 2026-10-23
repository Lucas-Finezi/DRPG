# Extração textual do SRD 5.2.1

Esta pasta contém o texto extraído de `source/SRD_CC_v5.2.1.pdf`. Ela é gerada por
`tools/extract/extract_srd.py` e **não deve ser editada à mão**: para corrigir algo,
ajuste o script e gere de novo.

## Fonte

| Campo | Valor |
|---|---|
| Arquivo | `source/SRD_CC_v5.2.1.pdf` |
| SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| Páginas | 364 (a página do PDF é igual ao número impresso, verificado nas 364 páginas) |
| Licença | CC-BY-4.0 (atribuição completa em `extraction_report.json` → `source.attribution`) |

## Arquivos

| Arquivo | Papel | Uso |
|---|---|---|
| `text/pdftotext/page-NNN.txt` | Texto bruto do poppler `pdftotext`, uma página por arquivo | Ferramenta independente para verificação cruzada |
| `text/pymupdf/page-NNN.txt` | Texto bruto do PyMuPDF na ordem de leitura do documento; células de tabela separadas por TAB | **Fonte autoritativa** para citar o texto exato |
| `SRD_CC_v5.2.1.md` | Markdown estruturado com marcadores `<!-- page N -->`, títulos, negrito/itálico, listas e tabelas | **Cópia de trabalho** dos lotes de extração (L00–L46) |
| `extraction_report.json` | Hash da fonte, versões das ferramentas, validação por página | Auditoria |
| `dehyphenation_log.json` | Cada palavra hifenizada em fim de linha e a decisão tomada no Markdown | Auditoria da hifenização |

Regra de uso: os lotes leem o Markdown, e toda entrada JSON gerada cita a página
(`source.page`). Em caso de dúvida, quem decide é o texto bruto da página.

## Validação

Para cada página, o script compara a contagem de cada caractere alfanumérico
entre as três saídas:

1. `pdftotext` × PyMuPDF (duas ferramentas independentes);
2. PyMuPDF × Markdown (a conversão para Markdown não pode perder nem inventar caracteres).

Resultado atual: **0 páginas com divergência**, em 1.051.815 caracteres
alfanuméricos. Como o Markdown só pode acrescentar pontuação (`#`, `*`, `|`, `-`) e
remover hífens de quebra de linha, qualquer perda ou invenção de texto aparece no
relatório.

## Transformações aplicadas no Markdown (e só nele)

- Rodapé removido (`N System Reference Document 5.2.1`), presente em todas as páginas.
- Hífen invisível (U+00AD) e espaço de largura zero (U+200B) removidos.
- **Hifenização de fim de linha:**
  - `pala-`/`vra` vira `palavra` quando o documento usa a forma sem hífen em outro lugar;
  - o hífen fica quando a forma hifenizada é a usada (ex.: `foot-wide`) ou quando
    vem depois de um número (`10-foot`).
  - Casos sem evidência são unidos e marcados `ambiguous` no log (98 casos, revisados
    à mão). Três compostos reais foram fixados no script (`KEEP_HYPHEN`).
- **Títulos:** o nível vem do tamanho da fonte do PDF (26pt → `#`, 18pt → `##`,
  ~14pt → `###`, 12pt → `####`, 10,5pt e seções de bloco de estatísticas → `#####`).
- **Tabelas:**
  - células na mesma linha de base viram `| a | b |`;
  - cabeçalhos com duas linhas aparecem como duas linhas de cabeçalho;
  - texto quebrado dentro de uma célula é anexado a ela;
  - células finais que o PDF guarda num bloco separado (quando uma célula do meio
    quebra, como em Light Crossbow) são reunidas à sua linha.
- **Linhas recuadas (`↳ `):** numa tabela com rótulos de grupo em itálico (ex.:
  *Saddle*, *Meal*, *Simple Melee Weapons*), uma linha impressa recuada sob o rótulo
  recebe o prefixo `↳ `. O recuo é medido em relação ao cabeçalho da mesma metade da
  tabela, porque algumas tabelas são impressas em duas metades lado a lado. Só assim
  se distingue `Saddle → Exotic` de `Sled`, que não pertence ao grupo.
- **Títulos quebrados em várias linhas** (ex.: "Curses and" / "Magical Contagions")
  são unidos num único título.
- **Negrito no texto corrido:** uma palavra em negrito que cai no início da linha só
  abre parágrafo quando é um rótulo terminado em `.`/`:` ou quando a linha anterior
  fechou a frase (ex.: "the **Otherworldly Steed** stat block"). Ênfases partidas pela
  quebra de linha (`**a** **b**`, `*Suc**cess:*`) são religadas.

## Limitações conhecidas

- **Atributos de monstros:** as células da tabela de atributos podem sair agrupadas
  de forma irregular (`**Dex** 18 +4 | +7`). A sequência é sempre atributo, valor,
  modificador, resistência.
- **Ordem de leitura:** a ordem segue a do documento do PDF (story order). Blocos
  laterais e tabelas podem aparecer fora do lugar visual; por exemplo, a continuação da
  tabela *Food, Drink, and Lodging* (p. 102) vem depois da tabela de veículos. O
  inventário (L00) trata esses casos explicitamente.
- **Ilustrações:** as 18 imagens do PDF não contêm texto e foram ignoradas.

## Como gerar de novo

```bash
pip install -r tools/extract/requirements.txt   # requer também poppler-utils (pdftotext)
python3 -I tools/extract/extract_srd.py source/SRD_CC_v5.2.1.pdf extraction
```

A execução é determinística: a mesma fonte e as mesmas versões de ferramenta
produzem saídas idênticas.
