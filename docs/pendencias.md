# Pendências para a versão definitiva dos arquivos do motor

Varredura de 24/10/2026 (`tools/validate/quality_scan.py`; resultado completo em
`inventory/dnd5e/srd-5.2.1/reports/quality_scan.json`). As verificações formais (schemas,
vocabulário, cobertura 17.306/17.306, refs, auditoria) passam. Os itens abaixo são o que
elas ainda não pegam.

## A. Bloqueiam o uso pelo motor

1. **Vocabulário de `data.rules` aberto.** Há 1.920 regras estruturadas em 1.051 entradas,
   com 1.917 chaves diferentes e nenhum schema. O motor não consegue interpretá-las de forma
   genérica. Correção: definir um vocabulário fechado por `id` de regra, ou converter em
   `effects` o que for executável, e validar com schema.
2. **Sem schema de tipo para 30 de 31 tipos.** Só `spell` tem `schema/kinds/*.schema.json`.
   Faltam, por exemplo, creature (336), magic-item (258), feature (303), rule (318), weapon,
   armor e gear. Correção: escrever os schemas e validar os `data`.
3. **Argumentos de predicado não conferidos.** São 52 chamadas em 12 padrões cujos argumentos
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

5. **170 efeitos `reference` apontando para a própria entrada**, com o comportamento só na
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

9. Escola de Flaming Sphere: Conjuration (D-001 estendido) ou Evocation.
10. D-002 (camada pt-BR): ainda não iniciada.
11. Espaço não separável: 352 ocorrências no texto, como no PDF. Normalizar ou manter literal?
12. 28 nomes registrados e nunca usados (4 predicados, 5 variáveis, 5 eventos e 9 stats).
    Remover ou manter para o motor?
13. Revisar os ~120 nomes novos de vocabulário (L31 e bestiário) e os quase-sinônimos, por
    exemplo `hp_at_most`/`hp_below`, `attack_is_ranged`/`attack_with_ranged_weapon` e
    `save_against_spell`/`save_against_spell_or_magic`.

## D. Texto (cosmético; o texto continua literal)

14. 8 parágrafos ainda cortados: Character Creation step 5, Combat Cover, os 2 exemplos de
    XP, Stat Block Overview e Truesight.
15. 4 listas de palavras em colunas impressas como linhas soltas: ações, áreas, condições e
    tipos de criatura.
16. Marcação quebrada "*Enlarge/**Reduce*" na Wand of Wonder (2 vezes).
