# Problemas encontrados por lote (L00–L46)

Relatório para revisão e correção. Para cada problema: o que aconteceu e o que foi feito.
Nada foi adicionado de fora do PDF. Todo texto das entradas é cópia fiel da fonte. Onde a
fonte tem defeito, o defeito ficou no texto e foi tratado na estrutura.

Legenda: **[fonte]** defeito do próprio PDF · **[extração]** defeito da conversão PDF→texto
· **[modelo]** escolha de modelagem que você pode querer revisar · **[pendente]** precisa da sua decisão.

## Itens que pedem sua decisão

1. **[pendente] Escola de Flaming Sphere (L27).** O D-001 diz que o cabeçalho da descrição vale
   para o acesso de classe. Estendi a mesma regra à escola: a descrição diz *Conjuration*
   (p. 132) e as listas de Druida, Feiticeiro e Mago dizem *Evocation*. Usei Conjuration.
   Confirme ou mude.
2. **[pendente] Habilidades de bloco de estatísticas não automatizadas (L33–L40).** Das cerca
   de 1.300 habilidades, 949 viraram efeitos automáticos. As demais ficaram como **decisão do
   mestre** (motivo `not_automatable`), com o texto original citado. Lista completa em
   `inventory/dnd5e/srd-5.2.1/reports/L33…L40_master_decisions.json`. Decida se quer
   modelar à mão as mais frequentes. Veja a tabela da L33–L40 abaixo.
3. **[modelo] Nomes novos de vocabulário.** Cerca de 120 nomes novos de predicados, eventos,
   variáveis e restrições foram registrados para itens mágicos e criaturas
   (`tools/build/l31_registry.py`, `monsterlib.REGISTRY`, além de um REGISTRY local em cada lote).
   Vale revisar nomes e granularidade.
4. **[modelo] Legendary Action** foi incluída em `system.action_economy`, com as regras
   literais da p. 257.

## Fase 0 — Fundamentos

**Extração (antes da L00)**
- [extração] Células de tabela partidas em blocos separados, títulos quebrados em várias
  linhas, negrito quebrado no meio da frase, glifos de controle (BEL) e marcadores de ênfase
  quádruplos. Tudo foi corrigido no extrator, com 0 divergência de caracteres entre
  pdftotext, PyMuPDF e o markdown nas 364 páginas.
- [extração] Os quadros laterais (sidebars) não têm marcação no texto. Foram detectados pela
  fonte sans-serif de 9 pt e marcados.

**L00 — Inventário**
- [fonte] 7 inconsistências internas registradas, resolvidas na L27. Veja a L27.
- [fonte] A tabela Travel Terrain está impressa dentro de "Creating a Background" (p. 192).
  Ela foi realocada para a L41. Skills foi para a L05 e Starting Equipment at Higher Levels
  para a L02.

**L01 / L02** — sem problema da fonte. A self-test negativa rejeita as 16 mutações.

## Fase 1 — Regras compartilhadas

- **L03.** Faltavam no vocabulário de efeitos as ops `restrict` e `auto_result`, o nível de
  condição e o custo de movimento. Foram adicionados. Aqui foram registrados os D-001 e D-002.
- **L04.** As tabelas Skills e Starting Equipment estão impressas fora da sua seção; foram
  marcadas como tabelas realocadas. As decisões de mestre foram modeladas: testes de
  escalada, tipo de dano improvisado, respostas preparadas e disposição em Influence.
- **L05.** Colisão de slug entre a seção Proficiency e o termo do glossário; a seção virou
  `rule/playing-the-game-proficiency`.
- **L06.** Nomes compartilhados entre glossário e itens de catálogo; `ref_of` passou a
  preferir o glossário.
- **L07 / L08** — nada relevante.
- **L09.** O teste de referências (`refs.py`) foi criado. A referência de Potions of Healing
  estava errada e foi corrigida.

## Fase 2 — Catálogos de personagem

- **L10.** [fonte] A tabela Elven Lineages está impressa na página do Goliath e foi realocada.
  A cobertura passou a tratar títulos de agrupamento sem texto como estrutura.
- **L11.** [fonte] A tabela Travel Terrain e sua nota de rodapé estão dentro de "Creating a
  Background". A nota tinha ficado na entrada da L11. Na L41 ela foi movida para a L41, e o
  texto da entrada `creating-a-background` mudou.
- **L12.** Algumas escolhas de equipamento inicial ficam em aberto na fonte; foram mantidas
  pelo nome.
- **L14.**
  - [modelo] "Magic action" não tinha representação; foi adicionada a propriedade `action`
    em `activation`.
  - O builder do Clérigo usava uma coluna de tabela inexistente. Foi criada a validação de
    colunas de lookup e a fórmula virou `scale`.
  - A regra `eldritch-invocation-options` estava duplicada (L12 e L14); foi removida da L14.
  - [extração] Fragmentos do cabeçalho de tabela ("——Spell Slots per Spell Level——",
    "**Level**") vazavam para os textos e foram incorporados à tabela.
  - Os títulos "Level N: X" ficavam sem cobertura; o prefixo agora é ignorado e o nível vai
    para as facets.
  - [extração] Parágrafos cortados no meio da frase em vários lotes. Foram criadas regras de
    rejunção e os textos foram corrigidos (Acolyte, Long Rest, Short Rest, Spell Level, Hit
    Points, Soldier).
- **L15 / L16** — nada relevante. A tabela Starting Equipment at Higher Levels ficou na L02.

## Fase 3 — Magias

- **L17.** [extração] Linhas de cabeçalho quebradas dentro de parênteses e linhas de Duration
  fundidas com a descrição; ambas corrigidas no render.
- **L18–L26.**
  - [fonte] 12 magias usam "Component:" no singular; o parser aceita.
  - [fonte] O fim de **Find the Path** está impresso dentro de Find Steed (p. 131). Os fins de
    **Antilife Shell** (p. 109) e **Antipathy/Sympathy** (p. 110) estão intercalados nas
    magias vizinhas, e um deles estava colado à última linha de Animate Objects. Foram
    registrados como fragmentos realocados, com divisão de nó; o texto ficou intacto.
  - [fonte] **Telekinesis** termina no meio da frase ("such as manipulating a simple tool,",
    p. 168). Foi registrado como inconsistência e modelado como decisão do mestre
    (`ambiguous_source`).
  - O índice de regra de Glyph of Warding estava errado; foram criados os ponteiros
    `rule:<id>`.
  - Três magias de nível 5 estavam faltando; o `refs.py` passou a acusar entradas esperadas
    ausentes.
  - [fonte] Create Undead tem custo "150+ GP" sem "worth"; a expressão regular foi corrigida.
- **L27.** [fonte] Divergências entre listas impressas e descrições, resolvidas pelo D-001 e
  registradas em `inconsistencies`:
  - Phantasmal Force: falta nas listas de Bardo, Feiticeiro e Mago;
  - Mind Spike: falta na lista de Feiticeiro;
  - Flaming Sphere: escola diferente nas listas de Druida, Feiticeiro e Mago (veja o item
    pendente 1).

  As marcações C/R/M conferem.

## Fase 4 — Equipamentos e itens

- **L28.** Títulos como "Light", "Range", "Reach" e "Slow" repetem-se em outras seções; foram
  desambiguados por página. Os rótulos de grupo da tabela Weapons viraram dados de categoria.
- **L29.** [modelo] A seção "Armor Training" (Equipment) colidia com o termo do glossário da
  L08 e sobrescrevia aquela entrada. A seção virou `equipment-armor-training`, e o
  `write_entry` agora recusa sobrescrever entrada de outro lote. [extração] O parágrafo
  "Category… falls into a category:" / "Light, Medium, or Heavy." foi rejuntado.
- **L30.**
  - [fonte] Glass Bottle "holds up to **11/2** pints": o ½ se perdeu. Ficou como decisão
    `ambiguous_source`.
  - [fonte] As linhas Amulet, Emblem e Reliquary da tabela Holy Symbols não têm entrada no
    inventário (lacuna da L00). Ficaram em `data.forms` do Holy Symbol.
  - [fonte] A tabela Food, Drink, and Lodging está intercalada com Airborne and Waterborne
    Vehicles (pp. 101–102); foram separadas pelo número de colunas.
  - [fonte] A tabela Adventuring Gear invade as seções de Ammunition e dos focos; foi
    removida delas.
  - Rótulos de grupo de tabela (*Saddle*, *Inn stay*) vazavam para linhas não recuadas. Era
    um bug do itemlib, corrigido.
  - Spell Scroll tem preço em lista ("(Cantrip, 30 GP; Level 1, 50 GP)"); foi para
    `data.cost.by_spell_level`.
  - [modelo] A luz em raio não tem forma de área no registro; foi gravada sem forma.
    Bullseye Lantern usa `cone`.
- **L31.**
  - [fonte] A tabela de alavancas do **Apparatus of the Crab** está impressa depois de Armor
    of Resistance, e a coluna "Down" da alavanca 5 saiu como parágrafo. A tabela foi
    reconstruída e movida.
  - [fonte] O bloco **Giant Fly** interrompe a Figurine of Wondrous Power (p. 222), que
    continua depois dele. O texto foi costurado em volta, e o bloco termina na linha CR.
  - [extração] Nomes em negrito quebrados ("**Giant**" / "**Goat**") e quebras de linha com
    espaço final ("Heavily " / "Obscured", "While " / "Frightened"). Foram criadas duas regras
    de rejunção; a segunda também corrigiu "Monk’s" / "Unarmored Defense" na L16.
  - [extração] Tabelas de cargas de cajados e varinhas com cabeçalho partido e duas magias
    por linha; Dragon Orb e Staff of Healing também ("(maximum 4…)" saiu como parágrafo).
    Foram reconstruídas.
  - [fonte] Cabeçalhos de tabela repetidos na quebra de página em sete tabelas (Bag of Beans,
    Deck of Illusions, Mysterious Deck e outras). Foram ignorados nos dados.
  - [fonte] Wand of Wonder tem marcação quebrada "*Enlarge/**Reduce*" (duas vezes).
    Quarterstaff of the Acrobat tem o rótulo partido em dois parágrafos. Shield of the
    Cavalier tem "***Forceful Bash*****.**". Os textos foram mantidos literais.
  - [fonte] Paired Items cita "*Boot of Striding and Springing*" e "*Boot of Elvenkind*" no
    singular. Foram mantidos literais, sem link.
  - [modelo] "demons" é uma tag de criatura, não um tipo; foi criado o predicado
    `creature_has_tag`.
  - [modelo] Efeitos que não se automatizam (cartas do Mysterious Deck, ilusões, efeitos do
    tipo Wish) viraram `reference` com nota e decisões do mestre onde o texto diz que o
    mestre decide.
  - [modelo] Slugs: `rule/magic-item-attunement` e `rule/using-magic-items`, porque
    `rule/attunement` já existia.
- **L32.**
  - [extração] Serpent Venom: "taking " / "10 (3d6)" foi rejuntado.
  - [fonte] A tabela do Spell Scroll tem cabeçalho repetido.
  - [modelo] Elixir of Health aponta para `rule/magical-contagions`, e a cópia para o
    grimório aponta para `feature/wizard-spellcasting`, porque não há entrada própria de
    spellbook.
  - Perícias e idiomas eram refs inexistentes (`dnd5e/skill/…`, `dnd5e/language/…`); viraram
    ids do sistema.

## Fase 5 — Criaturas e encontros

**L33–L40 (bestiário)**
- [extração] Os dados usam espaço não separável ("2d8 +\xa05"). Foi normalizado só nos
  dados; o texto ficou literal.
- [fonte] Os três últimos parágrafos do quadro **Running a Monster** estão impressos depois
  da seção Initiative (p. 254), sem moldura. Foram devolvidos ao quadro.
- [extração] Stat Block Overview: "This section provides a monster’s" / "Bonus Actions, if
  any." ficou partido (literal).
- O bloco do Giant Fly tem a linha AC em formato de tabela; o parser foi ajustado.
- Bug corrigido: dano extra condicional ("plus 2 (1d4) … if the attack roll had Advantage")
  era aplicado sempre. Agora fica para a decisão de complemento.
- **[pendente]** Habilidades automatizadas, com decisão de complemento e com decisão do mestre:

  | Lote | Automatizadas | Decisão (complemento) | Decisão do mestre |
  |---|---|---|---|
  | L33 | 282 | 50 | 29 |
  | L34 | 86 | 12 | 16 |
  | L35 | 172 | 35 | 23 |
  | L36 | 34 | 5 | 5 |
  | L37 | 76 | 17 | 18 |
  | L38 | 76 | 13 | 13 |
  | L39 | 117 | 36 | 26 |
  | L40 | 106 | 20 | 27 |

  Os padrões mais frequentes ainda manuais:
  - saves com "First/Second/Subsequent Failure" (mordidas venenosas, sopros de filhotes de
    dragão);
  - Shape-Shift (13);
  - Swallow e Engulf;
  - restaurações com condições especiais;
  - riders de Bite/Gore/Claw com condição ("If the target is a Humanoid, it is subjected
    to…").

**L41**
- [fonte] A nota de rodapé da Travel Terrain foi movida da L11 para a L41.
- [extração] Sample Fear DCs: só o cabeçalho é linha de tabela; os exemplos e as CDs saíram
  como parágrafos. A tabela foi reconstruída.
- [extração] Sample Mental Stress Effects tem o cabeçalho partido em duas linhas.
- [extração] A lista de Hazards ("Burning Dehydration" / "| Falling Malnutrition | Suffocation
  |") ficou quebrada. Foi coberta com refs.
- [extração] Truesight: "normal and magical" / "Darkness." partido (literal).
- [fonte] Fire-Casting Statue tem Trigger e Duration na mesma linha. As fórmulas de Special
  Movement estão quebradas no meio da linha.

**L42**
- [extração] O cabeçalho da XP Budget per Character está partido e foi reconstruído.
- [extração] Os exemplos estão cortados ("four level" / "1 characters") e o Exemplo 3 está
  colado ao último item do Exemplo 2 (literal).
- Nada foi adicionado além da fonte: nem multiplicadores, nem fórmulas extras.

## Fase 6 — Integração e auditoria

- **L43.** Grafo de refs com 1.952 nós, 4.117 arestas e 0 não resolvidas. 883 entradas não
  recebem nenhuma referência (esperado para seções e criaturas).
- **L44.** Manifest com 1.951 entradas. 27 nomes repetidos entre entradas do mesmo tipo
  (Ability Score Improvement por classe, Darkvision por espécie etc.) são esperados.
- **L45.** 21 cenários de comportamento passam. O cenário do Goblin Warrior revelou o bug do
  dano condicional, já corrigido.
- **L46.** 1.747/1.747 entradas do inventário presentes, 17.306/17.306 nós da fonte cobertos,
  0 duplicadas e 0 refs pendentes. Detalhes em `docs/audit.md`.
