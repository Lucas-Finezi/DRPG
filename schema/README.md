# Contrato de dados do DRPG (L01)

Os JSON Schemas (draft 2020-12) desta pasta são a **fonte única de verdade** do formato.
Todo conteúdo, oficial ou homebrew, é validado contra eles por
`tools/validate/validate.py`.

| Schema | Papel |
|---|---|
| `common` | Tipos compartilhados: `ref`, `slug`, `identifier`, nome de registro, lote, ponteiro JSON |
| `source` | Proveniência: sistema, documento, páginas, seção, licença, lote extrator; homebrew com `owner` |
| `expression` | Gramática fechada de números e dados: constante, `NdF`, `var`, `dice`, aritmética, `lookup` em tabela, `scale` em degraus |
| `duration` | Duração: instantânea, rodadas/minutos/horas/dias, até um evento, até ser dissipada, enquanto um predicado valer, concentração |
| `target` | Alvo: tipo, quantidade (expressão), alcance, área (formato registrado), filtros (tipos de criatura, tamanhos, voluntário...) |
| `effect` | **Vocabulário fechado de `op`** que o motor executa |
| `master_decision` | Ponto em que o mestre decide; mostra o texto literal da fonte e só as opções que a fonte oferece |
| `catalog_entry` | Envelope de toda entrada de catálogo (magia, criatura, item, classe, feature, condição, regra...) |
| `system` | Definição do sistema, incluindo os **registros** que fecham o vocabulário |

## Vocabulário de efeitos (`op`)

| Grupo | `op` |
|---|---|
| Vida | `damage`, `heal`, `temp_hp` |
| Condições | `apply_condition`, `remove_condition` |
| Modificadores | `modifier` (soma/define/mín./máx./multiplica um stat), `roll_mode` (vantagem/desvantagem), `auto_result` (falha/sucesso/acerto/erro/crítico automático), `reroll`, `restrict` (algo que a criatura não pode fazer), `defense` (resistência/imunidade/vulnerabilidade), `proficiency`, `sense`, `speed` |
| Recursos | `resource` (define máximo e recuperação), `spend`, `restore` |
| Resolução | `save`, `attack`, `check` (com ramos `on_fail`/`on_success`/`on_hit`...) |
| Ações e fluxo | `trigger` (evento → efeitos), `activation` (custo de ação → efeitos), `choice`, `repeat`, `end_effect` |
| Mundo | `move`, `grant`, `cast_spell`, `summon`, `transform` |
| Encaminhamento | `reference` (regra compartilhada), `master_decision` |

Todo nome usado dentro de um efeito precisa estar declarado em
`knowledge/<sistema>/system.json → registries`; o validador rejeita qualquer nome desconhecido. Isso vale para:
- variáveis, stats, rolagens, eventos, predicados e frequências;
- tipos de dano, tamanhos, tipos de criatura, áreas, sentidos e modos de movimento;
- atributos, perícias e custos de ação.

Ampliar a automação significa adicionar um `op` ou um nome de registro, com teste; o conteúdo nunca carrega código.

## Tiers

| Tier | Significado |
|---|---|
| 0 | Só texto de referência (sempre presente nas entradas oficiais) |
| 1 | Dados estruturados em `facets`/`data` ou no `system.json` |
| 2 | Efeitos declarativos (`effects` obrigatório) |
| 3 | Casos de borda que dependem do mestre (`master_decisions` obrigatório) |

## Cobertura: nenhuma regra perdida

Toda entrada oficial traz `text`, o texto literal da fonte, e `coverage`, uma
partição desse texto em segmentos consecutivos. Cada segmento é de um dos tipos:
- **structured:** representado por ponteiros (`/effects/0`, `/data/...`) ou por um ponto do sistema (`dnd5e/system/dnd5e#/core_rules/2`);
- **shared_rule:** remete a outra entrada (`dnd5e/condition/paralyzed`);
- **master_decision:** depende do mestre (`md:<id>`);
- **descriptive:** texto sem mecânica.

O validador prova que os segmentos, concatenados, reproduzem `text` exatamente e que
cada ponteiro resolve. Já `tools/validate/coverage.py` prova que cada parágrafo,
tabela e título da fonte atribuído a um lote está no texto de alguma entrada daquele lote.

## Refs, molde × estado e homebrew

- **Refs:**
  - `ref` estável no formato `<sistema>/<kind>/<slug>` (homebrew: `custom/<dono>/<kind>/<slug>`);
  - todo vínculo é feito por `ref`, nunca por nome;
  - o próprio sistema é `dnd5e/system/dnd5e`.
- **Molde × estado:** o catálogo é o molde imutável. O estado de jogo (PV atuais, condições, recursos gastos) guarda o `ref` do molde e evolui sozinho.
- **Homebrew:** usa o mesmo schema, com `extends` (entrada base) e `overrides` (JSON Merge Patch, RFC 7396). Entradas oficiais não podem ter `extends`/`overrides`, e o catálogo original nunca é modificado.

## Exemplos

Em `examples/`, cada `<schema>[.<rótulo>].example.json` valida contra `<schema>` e
usa texto real do SRD 5.2.1:
- Poisoned;
- Fireball (resistência, área, dano escalonado, decisão do mestre);
- Hold Person (alvos que escalam, teste repetido, concentração);
- Shield (gatilho de reação, bônus até um evento);
- uma Bola de Fogo homebrew derivada da oficial;
- um trecho do `system.json`.

`tools/validate/selftest.py` muta esses exemplos e confirma que o validador rejeita cada erro.
