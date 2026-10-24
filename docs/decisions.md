# Decisões do projeto

Registro de decisões que afetam a extração. Cada decisão tem um id citado pelos dados
e pelas ferramentas que a aplicam.

## D-001 — Acesso de classe a magias vem do cabeçalho da descrição

**Decisão (do responsável pelo projeto):** a lista de classes no cabeçalho da descrição de
cada magia (ex.: *Phantasmal Force* — "Level 2 Illusion (Bard, Sorcerer, Wizard)") é a
fonte de verdade para habilitar a magia em cada classe. As listas de magia por classe
(capítulo "Classes") são conferidas contra ela; quando divergem, prevalece o cabeçalho.

**Casos conhecidos na fonte (L00):**
- *Phantasmal Force* (p. 151): cabeçalho cita Bard, Sorcerer e Wizard; nenhuma lista de
  classe a inclui. → habilitada para Bard, Sorcerer e Wizard.
- *Mind Spike* (p. 149): cabeçalho cita Sorcerer, Warlock e Wizard; a lista do Sorcerer
  não a inclui. → habilitada também para Sorcerer.

A escola da magia **não** segue esta regra no caso de *Flaming Sphere*: ver D-003.

Aplicada por: `tools/inventory/build_inventory.py` (campo `resolution`) e pelo lote L27: cada
entrada `spell-list` guarda a lista impressa (`printed_spells`), a lista efetiva (`spells`, que
inclui as magias cujo cabeçalho cita a classe) e as divergências em `inconsistencies`.

## D-003 — Escola de Flaming Sphere

**Decisão (do responsável pelo projeto, 24/10/2026):** *Flaming Sphere* é uma magia de
**Evocation**. O cabeçalho da descrição (p. 132) diz Conjuration; as listas de Druid, Sorcerer
e Wizard (pp. 44, 68, 80) dizem Evocation. Prevalecem as listas. A entrada da magia registra a
divergência em `inconsistencies` com `decision: D-003`.

Aplicada por: `tools/build/spelllib.py` (`SCHOOL_DECISIONS`) e pelo campo `resolution` do
inventário.

## D-002 — Idioma

Os arquivos de dados ficam em inglês, como a fonte. Uma camada de tradução pt-BR será
criada depois, em arquivo separado, sem alterar as entradas. **Adiada** (24/10/2026): fora do
escopo por enquanto.

## D-004 — Vocabulário canônico do motor

**Decisão (do responsável pelo projeto, 24/10/2026):** os registros são unificados para que
o motor de regras implemente **um predicado por conceito**. Famílias de nomes específicos
viram um predicado com parâmetros, por exemplo:
- `item_state {item, state}`, no lugar de `wearing_item`, `wielding_item`, `holds_item`,
  `attuned_to_item` e mais 7;
- `attack_is {range, via, item, property, weapon_kind, attack_kind}`, no lugar de 18
  variantes;
- `save_against`, `check_uses`, `creature_is`, `hp_is`, `spell_level_in`, `within_feet`,
  `level_at_least`, `in_light`, `obscured`, `can_see`, `has_condition` e `spell_of_class`.

Resultado: 221 → 153 predicados e 108 → 106 eventos. Argumentos com nome divergente foram
padronizados (`deals_damage_type {damage_type}`, `behind_cover {degree}`,
`has_speed {movement_mode}`).

Aplicada por: `tools/build/vocabulary.py` (aliases e definições canônicas), na escrita de
cada entrada e do `system.json`. O validador passa a recusar argumentos de predicado fora
dos `params` declarados e parâmetros pontuados (`x.y`) em nomes sem parâmetros. O self-test
ganhou 2 casos negativos.

## D-005 — Contrato de execução entre o catálogo e o motor

**Decisão (24/10/2026, a partir da simulação `docs/simulacao-goblins.md`):** toda mecânica que
o motor precisa executar fica em campo estruturado; a nota (`note`) só esclarece. Quando um
dado não cabia no vocabulário, o vocabulário foi estendido, sem conteúdo externo ao SRD:

| Regra do contrato | Onde |
|---|---|
| Fórmulas derivadas ficam no registro: `registries.<nome>.formula` (+ `formula_source`) copiadas de `levels.rules` (CD de magia, bônus de ataque mágico, CA base) | `vocabulary.link_formulas`, `system.schema.json` |
| Ganho de PV é expressão na classe: `data.hit_points {level_1, per_level {roll, fixed}}`, a partir das duas tabelas de PV por classe e de "Gaining a Level" | `l12_classes.py` |
| Equipamento concedido é `grant {items, gp}` (classes e antecedentes); `grant` aceita `items`, `gp` e `filter {spell_level, school}` para listas de magias | `effect.schema.json`, `l11`, `l12`, `l15` |
| Alternativas são `choice`, nunca efeitos lado a lado (Golpe Desarmado, Nimble Escape, Cunning Action, aumento de atributos do antecedente, linhagens de elfo e legados de tiefling) | `l04`, `monsterlib`, `l11`, `l14_species_traits` |
| Subclasse concede cada característica com `when: level_at_least {class, level}` | `l13_subclasses.py` |
| Uma `activation` com `duration` torna a própria entrada ativa (`effect_active`) por essa duração (Fúria) | `l14_barbarian.py` |
| Condição implícita sem `duration` dura até ser removida; a que termina junto com a condição-mãe declara `while: has_condition` (Incapacitated em Paralyzed, Petrified, Stunned e Unconscious) | `l03_conditions.py` |
| Cair a 0 PV: Unconscious com `while: hp_is {zero}` | `l06_damage.py` |
| Efeito sem `duration` dentro de um gatilho vale só para a chamada que o disparou (ex.: Deflect Attacks reduz o dano daquele ataque) | motor |
| Momento de um teste repetido é um `trigger` com evento, e o fim antecipado é `ends_on` (Sleep: 2ª salvaguarda no fim do próximo turno; o efeito acaba com dano) | `l18_level1.py` |
| "Só a próxima jogada contra o alvo" é `ends_on: targeted_by_attack_roll` (consumido pela jogada); "só para quem aplicou" é `when: roller_is_source` (Guiding Bolt, Vex) | `l18`, `l28` |
| Ataque extra sem modificador de atributo no dano: `attack.ability_modifier_to_damage: negative_only` (Cleave, propriedade Light) | `l28_weapons.py` |
| Limite de nível na recuperação de espaços: `restore.max_level` (Arcane Recovery, Natural Recovery) | `l14_wizard.py`, `l14_druid.py` |
| `cast_spell.spell` pode ser a magia escolhida antes (`{"var": "chosen.<id>"}`), como em Magic Initiate | `effect.schema.json`, `l15_feats.py` |
| Argumento de item é o slug do catálogo (`holy-symbol`) | `l14_cleric.py` |

Novos nomes: o predicado `roller_is_source` e o evento `targeted_by_attack_roll`.

Verificação: `tests/engine/test_goblin_simulation.py` (10 sementes: zero `DATA_GAP` e zero
`ENGINE_GAP`) e `tools/validate/engine_contract.py`, que confronta o uso no catálogo inteiro
com o que o protótipo executa. Ambos rodam em `run_all.py`.
