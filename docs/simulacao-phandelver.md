# Simulação de campanha: dois grupos de 6 aventureiros, nível 1 ao 5

O protótipo de motor (`tools/engine/`) jogou do início ao fim uma aventura publicada para
5e, fornecida pelo usuário em PDF. Foram dois grupos com classes excludentes; juntos eles
usam as 12 classes do catálogo.

> **A aventura não é base de conhecimento.** O livro serviu só para montar o roteiro da
> simulação, que fica em `simulations/phandelver/`, fora de `knowledge/`. Nada do livro
> entrou no catálogo `knowledge/dnd5e`:
> - nenhuma criatura, item, regra ou texto;
> - o motor lê apenas o catálogo do SRD 5.2.1;
> - criaturas e itens que não existem no SRD foram trocados por equivalentes do SRD
>   (seção 2).

Para rodar:

```
python3 -I -m simulations.phandelver.run                   # semente 2026 narrada, A e B
python3 -I -m simulations.phandelver.run --batch 20        # + 20 sementes por grupo
python3 -I -m unittest discover -s tests/engine -v         # testes (inclui a campanha)
```

O resultado fica em `reports/simulation/phandelver.json`. Ele traz:
- as fichas iniciais e finais;
- as cenas, os níveis, as mortes e os saques;
- a narrativa rolada;
- o registro de todas as chamadas ao catálogo.

## 1. Montagem

| Grupo A | Espécie | Antecedente | Grupo B | Espécie | Antecedente |
|---|---|---|---|---|---|
| Fighter (Champion) | human | soldier | Paladin (Devotion) | dragonborn | soldier |
| Cleric (Life) | dwarf | acolyte | Druid (Land) | gnome | sage |
| Rogue (Thief) | halfling | criminal | Barbarian (Berserker) | goliath | soldier |
| Wizard (Evoker) | elf | sage | Monk (Open Hand) | human | criminal |
| Ranger (Hunter) | orc | soldier | Sorcerer (Draconic) | elf | sage |
| Bard (Lore) | tiefling | criminal | Warlock (Fiend) | tiefling | acolyte |

Os dois grupos juntos cobrem as 12 classes, as 12 subclasses do SRD, as 9 espécies e os
4 antecedentes.

- **Escolhas do jogador:** perícias, estilos de luta, maestrias, magias, invocações, ASI e
  subclasse. Um `Chooser` (`tools/engine/party.py`) decide, com prioridades fixas por
  classe, e cada escolha é registrada.
- **Equipamento inicial:** vem da classe e do antecedente, como está no catálogo.
- **PV:** no nível 1, o máximo do dado de vida + CON. A cada nível novo, **o dado de vida é
  rolado** (`hit_points.per_level.roll` da classe) e somado à CON.

## 2. Roteiro e substituições

O roteiro (`simulations/phandelver/scenario.py`) segue as quatro partes do livro e um
epílogo. Ele usa os encontros, as armadilhas, as CDs, os tesouros e as recompensas de XP
de cada área e da história. As viagens rolam encontros aleatórios nas tabelas do livro.

Criaturas fora do SRD foram trocadas pelo equivalente do SRD mais próximo em ND e papel
(decisão de mestre, registrada como `GM`):

| No livro | No catálogo SRD |
|---|---|
| Nothic, Spectator | gibbering-mouther |
| Evil mage, Nezznar | cultist-fanatic |
| Orc / Brughor | gnoll-warrior / tough-boss |
| Redbrand ruffian | tough |
| Twig blight | awakened-shrub |
| Ash zombie | zombie |
| Flameskull | wight |
| Venomfang | young-green-dragon (foge com metade dos PV, como no livro) |
| King Grol / Targor / Mormesk | bugbear-stalker / hobgoblin-captain / wraith |

Itens com nome próprio usam a entrada genérica do SRD:
- Talon, Hew e Lightbringer → `weapon-plus1-plus2-or-plus3` (+1);
- Dragonguard → `armor-plus1`.

O Staff of Defense e o Spider Staff não têm entrada no SRD. Eles ficam no inventário só
pelo nome, sem mecânica (`GM`).

## 3. Regras de campanha aplicadas

- **Recursos:**
  - espaços de magia e Pact Magic;
  - Rage, Ki/Focus, Channel Divinity, Wild Shape, Bardic Inspiration, Sorcery Points,
    Lay on Hands, Second Wind e Action Surge;
  - Heroic Inspiration, cargas de varinha, poções e pergaminhos.

  Tudo é gasto em combate e recuperado só no descanso certo.
- **Descansos:**
  - **descanso curto** depois da luta, se o grupo está ferido: no máximo 2 seguidos, e
    gasta dados de vida rolados;
  - **descanso longo** nos pontos seguros do roteiro;
  - Mage Armor e Armor of Shadows são lançadas pela manhã.
- **Recompensas:**
  - moedas divididas por igual;
  - objetos de valor para quem tem menos riqueza;
  - itens mágicos para quem melhor os usa, com sintonia de no máximo 3 e no máximo uma
    arma mágica por pessoa enquanto houver outra opção.

  Tudo vai para o inventário (`items`, `inventory`, `coins`) e aparece nas fichas finais.
- **XP e marcos:** o XP vem das recompensas do livro, por área e por história. Os níveis
  sobem quando o XP alcança a tabela do `system.json`.

  Com 6 personagens, o XP do livro (pensado para 4 a 5) dividido não alcança os
  limiares. Por isso os **marcos do livro** são aplicados como decisão de mestre:
  - nível 3 durante a Parte 2;
  - nível 4 antes da Parte 4;
  - nível 5 no final.

  O grupo termina com 4.000 a 5.200 XP, abaixo dos 6.500 do nível 5. Para que as
  habilidades do nível 5 sejam usadas em jogo, o epílogo força encontros errantes na
  caverna.
- **Morte:** com 3 falhas no teste contra a morte, o personagem morre.
  - O grupo tenta revivê-lo com pergaminho ou magia de Revivify mais diamante de 300 po.
  - Se não der, vale "Character Demise" do SRD: um personagem novo, da mesma montagem,
    entra no nível do grupo no próximo descanso longo (Bard II, Monk III…).
  - Personagem estabilizado ganha 1 PV depois de 1d4 horas (`GM`).
- **Derrota do grupo:** segue a consequência do livro. O grupo acorda roubado das moedas,
  faz um descanso longo e tenta de novo, no máximo 3 vezes.

## 4. Resultado da semente narrada (2026)

Os dois grupos terminaram a campanha no nível 5. Cada um foi derrotado uma vez, na
Wave Echo 11 (5 bugbears), e venceu na segunda tentativa.

| | Grupo A | Grupo B |
|---|---|---|
| Cenas | 77 (54 combates) | 80 (57 combates) |
| Descansos | 35 | 37 |
| Saques registrados | 33 | 33 |
| Mortes | Bard (revivido por pergaminho; morre de novo depois), Cleric e Wizard (Wave Echo 9, ghouls) | Monk (Venomfang), Monk II (revivido, depois morto), Druid |
| Substitutos | Bard II, Cleric II, Wizard II | Monk II, Monk III, Druid II |

### PV ganhos por nível (dado de vida rolado + CON)

| Personagem | Nv 2 | Nv 3 | Nv 4 | Nv 5 | PV final |
|---|---|---|---|---|---|
| Fighter (d10) | 12 | 8 | 12 | 5 | 49 |
| Rogue (d8) | 5 | 3 | 8 | 8 | 34 |
| Ranger (d10) | 3 | 10 | 5 | 10 | 40 |
| Cleric II (d8) | 8 | 3 | 5 | 3 | 33 |
| Wizard II (d6) | 5 | 4 | 8 | 5 | 30 |
| Bard II (d8) | 3 | 8 | 9 | 9 | 38 |
| Paladin (d10) | 8 | 6 | 11 | 6 | 43 |
| Barbarian (d12) | 8 | 8 | 11 | 11 | 52 |
| Sorcerer (d6) | 5 | 4 | 7 | 4 | 34 |
| Warlock (d8) | 4 | 5 | 6 | 6 | 30 |
| Druid II (d8) | 9 | 7 | 5 | 7 | 38 |
| Monk III (d8) | 10 | 10 | 8 | 10 | 48 |

Todos os ganhos ficam entre 1 + CON e o máximo do dado + CON. O Cleric (dwarf) soma
mais 1 por nível pelo *Dwarven Toughness*.

### Habilidades adquiridas no nível 5 (exemplos das fichas finais)

- **Fighter:**
  - Action Surge, Tactical Mind, Tactical Shift, Extra Attack;
  - Champion: Improved Critical, Remarkable Athlete;
  - ASI (STR 19).
- **Paladin:** Paladin's Smite, Channel Divinity, Sacred Weapon, Extra Attack, Faithful Steed;
  espaços 4/2.
- **Warlock:** Pact Magic com 2 espaços de nível 3, Armor of Shadows, Magical Cunning,
  Dark One's Blessing.
- **Wizard, Cleric, Bard, Druid, Sorcerer:** espaços 4/3/2, e cada um com as
  características do nível 5 da sua classe.

### Inventários finais (itens de destaque)

| Personagem | Itens | Riqueza (po) |
|---|---|---|
| Fighter | Talon (+1 longsword), Dragonguard (+1 breastplate) | 232 |
| Rogue | Ring of Protection, Potion of Invisibility, Potion of Flying | 273 |
| Ranger | Wand of Magic Missiles | 376 |
| Cleric II | Lightbringer (+1 mace), Potion of Healing | 393 |
| Bard II | Boots of Striding and Springing | 406 |
| Paladin | Talon, Wand of Magic Missiles, Spell Scroll (Silence), Potion of Healing | 282 |
| Barbarian | Hew (+1 battleaxe), Ring of Protection | 273 |
| Sorcerer | Scrolls de Darkness, Misty Step e Lightning Bolt, Potion of Healing | 256 |
| Warlock | Potion of Flying | 641 |
| Druid II | Dragonguard, Potion of Vitality | 585 |

Os dois grupos encontram os mesmos tesouros, mas a distribuição muda com a composição.

## 5. Lote: 20 sementes por grupo

| | Grupo A | Grupo B |
|---|---|---|
| Campanhas concluídas | 20/20 | 20/20 |
| Todos no nível 5 ao final | 120/120 | 120/120 |
| Mortes (total; sem retorno) | 50; 41 | 60; 51 |
| Campanhas sem mortes | 2 | 2 |
| Derrotas do grupo (com nova tentativa) | 22 | 41 |

A campanha é mortal para 6 personagens jogados por táticas automáticas. Os picos são
Venomfang, o castelo e a Wave Echo (ghouls, bugbears, o wight no lugar do flameskull).
O grupo B, com mais personagens corpo a corpo e o warlock com poucos espaços, perde mais.

## 6. Chamadas ao catálogo

Totais na semente narrada mais as 20 sementes:

| | OK | DATA_GAP | ENGINE_GAP | GM |
|---|---|---|---|---|
| Grupo A | 631.556 | 1.366 | **0** | 640 |
| Grupo B | 785.459 | 793 | **0** | 913 |

### Lacunas de dados encontradas (DATA_GAP)

Nenhuma delas impede o jogo. O motor usa um valor de reserva explícito e registra a
lacuna.

1. **Recarga só na nota:** o "Recharge 5–6" de giant-spider, young-green-dragon,
   doppelganger e gibbering-mouther está só na nota. O motor usa a habilidade uma vez por
   luta. Falta um campo estruturado `activation.recharge`.
2. **ASI:** a escolha do atributo não é declarada (`ability_score.chosen`). Vale a
   escolha do jogador.
3. **Bard:** a perícia tem `choose` sem `from`; as opções estão só na nota.
4. **Spell Scroll:** a ação de ler aponta para a própria entrada. O motor lança a magia
   guardada com a CD do pergaminho.
5. **Arma +1/+2/+3:** o bônus depende de `wielded`, e não de "ataque feito com esta
   arma". O motor aplica o bônus só aos ataques com a arma.
6. **Eldritch Invocations:** as opções estão só na nota (faceta `feature_type`). O motor
   lista as features que têm essa faceta.

### Decisões de mestre (GM)

- os marcos de nível;
- a derrota com nova tentativa;
- os personagens substitutos;
- o 1 PV do estabilizado;
- premissas de cena: iluminação e linha de visão;
- itens sem entrada no SRD.

### Habilidades adquiridas que nunca disparam

Elas existem nas fichas, mas o motor não as chamou em nenhuma cena:

- **Exploração e social, que o roteiro resolve como testes simples:**
  - Darkvision (todas as espécies), Trance, Naturally Stealthy;
  - Second-Story Work, Fast Hands, Ritual Adept, Hunter's Lore;
  - Jack of All Trades, Slow Fall.
- **Gatilhos que o motor ainda não emite:**
  - Cutting Words (`creature_roll_made`/`roll_succeeded`);
  - Tactical Mind (`fails_ability_check`);
  - Uncanny Dodge e Preserve Life (a tática não as escolhe);
  - Tactical Shift.
- **Recuperação de recursos que a tática não usa:** Font of Inspiration, Memorize Spell,
  Magical Cunning, Wild Resurgence, Land's Aid, Sear Undead, Cunning Strike.
- **Sem efeito estruturado no catálogo:** Metamagic (as opções estão só em `data.rules`).
- Dragonborn Damage Resistance não disparou porque nenhum ataque usou o tipo da
  ancestralidade.

## 7. O que mudou no motor

- **Novos módulos:**
  - `campaign.py`: cenas, XP, marcos, descansos, mortes, substitutos, derrota;
  - `party.py`: escolhas do jogador, equipamento, divisão do tesouro;
  - `tactics.py`: turnos de PCs e monstros para as 12 classes.
- **`engine.py`:**
  - Pact Magic e Wild Shape;
  - poções, varinhas e pergaminhos;
  - testes de habilidade com perícia e expertise;
  - testes de resistência repetidos;
  - rerrolagens (Halfling Luck), Bardic Inspiration, Hunter's Mark, Divine Smite;
  - Action Surge, Uncanny Dodge, Relentless Endurance, Great Weapon Fighting;
  - cerca de 20 predicados novos;
  - a op `sense` (Mind Spike) como efeito temporário.
- **`builder.py`:** subida de nível com PV rolado. A conjuração passou a ser genérica
  para todas as classes (preparadas, grimório, truques, Pact Magic).
- **Dado corrigido (D-005):** a proficiência marcial do monk e do rogue
  (`martial_with:<propriedade>`) estava num `from` sem `choose`. Isso foi corrigido em
  `l12_classes.py` e as entradas foram regeneradas.
- **Teste novo:** `tests/engine/test_phandelver_campaign.py` exige as 12 classes, a
  campanha concluída no nível 5, zero ENGINE_GAP e apenas as lacunas de dados conhecidas.
