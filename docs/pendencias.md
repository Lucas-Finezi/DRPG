# Pendências para a versão definitiva dos arquivos do motor

Varredura de 24/10/2026 (`tools/validate/quality_scan.py`; resultado completo em
`inventory/dnd5e/srd-5.2.1/reports/quality_scan.json`). As verificações formais (schemas,
vocabulário, cobertura 17.306/17.306, refs, auditoria) passam. Os itens abaixo são o que
elas ainda não pegam.

**Atualização (simulação dos goblins, D-005):**
- O encontro de 4 personagens contra 6 goblins, com subida ao nível 3, aplica 100% das
  chamadas a partir dos dados (`docs/simulacao-goblins.md`).
- Itens resolvidos: 3, 9 e o trecho de classes do 5.
- Nova seção E: o contrato do motor de produção.

## A. Bloqueiam o uso pelo motor

1. **Vocabulário de `data.rules` aberto.** Há 1.920 regras estruturadas em 1.051 entradas,
   com 1.917 chaves diferentes e nenhum schema. O motor não consegue interpretá-las de forma
   genérica. Correção: definir um vocabulário fechado por `id` de regra, ou converter em
   `effects` o que for executável, e validar com schema.
2. **Sem schema de tipo para 30 de 31 tipos.** Só `spell` tem `schema/kinds/*.schema.json`.
   Faltam, por exemplo, creature (336), magic-item (258), feature (303), rule (318), weapon,
   armor e gear. Correção: escrever os schemas e validar os `data`.
3. ~~**Argumentos de predicado não conferidos.**~~ **Resolvido (D-004):** 0 divergências, e o
   validador recusa novas. São 52 chamadas em 12 padrões cujos argumentos
   não batem com os `params` do registro:
   - `deals_damage_type` com `type` em vez de `damage_type` (16);
   - `ally_within_feet_of_target` com `not_incapacitated` não declarado (18);
   - `can_see`, `creature_type`, `behind_cover`, `has_speed`, `roll_is`, `roll_succeeded` e
     outros.

   Correção: padronizar os nomes e acrescentar essa checagem ao `validate.py`.
4. **27 ataques e salvaguardas de criaturas sem resultado.**
   - 11 ataques sem `on_hit`: enxames com "X damage, or Y damage if Bloodied" e mordidas
     com dano condicional;
   - 16 salvaguardas sem `on_fail`: sopros de dragões de cobre e ouro, Rust Monster e outros.

   A decisão de complemento existe, mas o efeito em si causa zero dano. Correção: modelar
   com `choice` ou `when`.

## B. Mecânica fora de campos executáveis

5. **170 → 144 efeitos `reference` apontando para a própria entrada.** O equipamento das
   classes virou `grant`, e a Fúria virou `activation.duration`. Restam magic-item 77,
   spell 48, rule 8, feature 7 e contagion/curse 4. Situação original: 170 efeitos, com o comportamento só na
   nota: magic-item 77, spell 48, class 25, feature 8, rule 8 e contagion/curse 4. Exemplos:
   classes com "Gain data.starting_equipment[0]", que deveria ser `grant`; `mounted-combat`
   com nota vazia.
6. **173 notas com números, dados ou CDs** que deveriam estar em campos: magic-item 95,
   spell 29, creature 14, gear 12 e outros.
7. **Habilidades de criatura para o mestre (L33–L40):**
   - 345 habilidades inteiras com decisão `not_automatable`;
   - 188 complementos (riders) também deixados ao mestre.

   Frequentes: salvaguardas com First/Second Failure, Shape-Shift, Swallow, Engulf,
   restaurações, riders condicionais. Correção: modelar os padrões recorrentes; o restante
   continua como decisão do mestre.
8. **Armadilhas:** os 16 `trigger`/`duration` estão só em texto. Correção: converter em
   evento e duração.

## C. Decisões suas

9. ~~Escola de Flaming Sphere~~ **Decidido (D-003):** Evocation.
10. D-002 (camada pt-BR): **adiada**.
11. Espaço não separável (U+00A0): 352 ocorrências no texto, herdadas do PDF (ex.: "2d8 +
    5", "10 feet"). É invisível e os parsers já o tratam como espaço. Normalizar para
    espaço comum ou manter literal?
12. 23 nomes registrados e nunca usados nas entradas (4 predicados, 5 variáveis, 5 eventos
    e 9 stats). O motor usa `level_gained`, `regains_hit_points` e `round_end`, que devem
    ficar. Os demais: remover ou manter?
13. Revisar os ~120 nomes novos de vocabulário (L31 e bestiário) e os quase-sinônimos, por
    exemplo `hp_at_most`/`hp_below`, `attack_is_ranged`/`attack_with_ranged_weapon` e
    `save_against_spell`/`save_against_spell_or_magic`.

## D. Texto (cosmético; o texto continua literal)

14. 8 parágrafos ainda cortados: Character Creation step 5, Combat Cover, os 2 exemplos de
    XP, Stat Block Overview e Truesight.
15. 4 listas de palavras em colunas impressas como linhas soltas: ações, áreas, condições e
    tipos de criatura.
16. Marcação quebrada "*Enlarge/**Reduce*" na Wand of Wonder (2 vezes).

## E. Contrato do motor de produção (`tools/validate/engine_contract.py`)

Relatório completo em `reports/engine_contract.json`. Não bloqueia os dados; é a lista do
que o motor definitivo precisa executar além do que o protótipo já faz.

17. **Entradas com efeitos executáveis pelo protótipo:** 952 de 1.391 (869 antes da simulação de campanha). Faltam as ops:
    - `cast_spell` (154 entradas);
    - `summon` (23);
    - `transform` (5);
    - `sense` (35), que exige um modelo de visão.
18. **Predicados e variáveis sem implementação no protótipo:**
    - 111 de 145 predicados, por exemplo `target_size_at_most` (42), `creature_is` (25) e
      `in_light` (8);
    - 29 de 44 variáveis.
19. **Campos ainda não lidos pelo protótipo:**
    - `activation.frequency` (104);
    - `apply_condition.params` (50);
    - `save.repeat` (31);
    - `defense.conditions` (17);
    - os campos de `summon` e `transform`.
20. **351 notas com palavras de regra** (*only*, *next*, *until*, *half*, *at the end*…). Nos
    caminhos da simulação, 5 de 18 notas escondiam mecânica: Sleep, Guiding Bolt, Vex,
    Cleave e Arcane Recovery, todas já corrigidas. Revisar as 351 com o mesmo critério
    (D-005).

## F. Encontradas na simulação de campanha (`docs/simulacao-phandelver.md`)

O motor seguiu em todos os casos, com valor de reserva registrado como `DATA_GAP`.

21. **Recarga só na nota.** "Recharge X–Y" de giant-spider, young-green-dragon,
    doppelganger e gibbering-mouther (e de outras criaturas do bestiário). Falta um campo
    `activation.recharge`.
22. **ASI sem escolha declarada.** `ability_score.chosen` é usado, mas não é uma escolha
    declarada na feat Ability Score Improvement.
23. **Perícias do Bard:** `choose` sem `from`; as opções estão só na nota.
24. **Spell Scroll:** a ação Read referencia a própria entrada.
25. **Armas +1/+2/+3:** o bônus depende de `item_state.wielded`, e não de "ataque com esta
    arma".
26. **Eldritch Invocations:** as opções estão só na nota (faceta `feature_type`).
27. **Gatilhos sem emissor no motor.** Cutting Words (`creature_roll_made`,
    `roll_succeeded`) e Tactical Mind (`fails_ability_check`). Metamagic não tem efeitos
    estruturados (só `data.rules`).
