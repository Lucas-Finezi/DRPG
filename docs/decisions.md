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
