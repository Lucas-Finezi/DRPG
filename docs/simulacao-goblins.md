# Simulação: 4 aventureiros de nível 2 contra 6 goblins, e a subida para o nível 3

Exercício teórico, executado de verdade por um protótipo de motor
(`tools/engine/`) que lê só o catálogo gerado a partir do SRD 5.2.1. A pergunta era se todas
as chamadas necessárias podem ser aplicadas: **sim, depois das correções deste lote**.

- Antes: 46 tipos de chamada não podiam ser aplicados a partir dos dados (29.812 ocorrências
  em 200 simulações).
- Depois: 0 lacunas de dados e 0 lacunas do motor, com 343.215 chamadas aplicadas.
- Só uma decisão fica com o mestre: a premissa de subir de nível (ver seção 4).

Para rodar:

```
python3 -I -m tools.engine.simulate_goblins              # semente narrada + 200 sementes
python3 -I -m unittest discover -s tests/engine -v       # o mesmo, como teste (10 sementes)
```

Os resultados ficam em `reports/simulation/goblins.json`. O mesmo motor rodado sobre os
dados anteriores às correções está em `reports/simulation/goblins_before.json`.

## 1. Como o motor funciona

- Cada chamada ao catálogo é registrada com um status:
  - **OK**: executada a partir de dado estruturado;
  - **DATA_GAP**: o catálogo não tem o que a chamada precisa (placeholder, mecânica só na
    nota, tabela só em texto);
  - **ENGINE_GAP**: o dado existe, mas o protótipo não o executa;
  - **GM**: a regra entrega a decisão ao mestre.
- Quando falta um dado, o motor usa um valor de reserva explícito e registra `DATA_GAP`.
  Assim nenhuma lacuna passa em silêncio.
- O que o motor executa:
  - efeitos: ataque, dano, cura, salvaguarda, condição, modificador, vantagem e
    desvantagem, defesa, restrição, recurso, gatilho, ativação, escolha, repetição,
    concessão (`grant`), referência, movimento e concentração;
  - predicados, variáveis, eventos e durações (inclusive "até o próximo turno" e
    `ends_on`);
  - crítico, morte de monstro a 0 PV, salvaguardas contra a morte e iniciativa em grupo
    para criaturas idênticas.
- Simplificações de cena (registradas como `GM` quando consultadas):
  - posições em uma linha (distância em pés);
  - luz plena e campo aberto, sem cobertura;
  - sem ataques de oportunidade;
  - a tática de cada criatura é uma política simples. Ela só toma decisões; o resultado de
    cada regra vem dos dados.

## 2. O grupo (só dados do catálogo)

Para cada personagem, o motor aplica:
- a matriz padrão da classe (tabela *Standard Array by Class*);
- o aumento de atributos do antecedente (+2/+1);
- espécie, talento de origem, perícias e equipamento inicial (opção A);
- o nível 1 e depois o nível 2, pelo mesmo procedimento de avanço de nível.

| | Mago | Clériga | Bárbaro | Monge |
|---|---|---|---|---|
| Espécie / antecedente | Elfo (Alto Elfo) / Sage | Anão / Acolyte | Golias (Fire Giant) / Soldier | Humano / Criminal |
| Talento de origem | Magic Initiate (Wizard) | Magic Initiate (Cleric) | Savage Attacker | Alert + Skilled (Versatile) |
| Atributos | For 8, Des 12, Con 14, Int 17, Sab 14, Car 10 | 14, 8, 13, 10, 17, 13 | 17, 13, 15, 10, 12, 8 | 12, 17, 14, 10, 14, 8 |
| PV no nível 2 → 3 | 14 → 20 | 17 → 24 (com Dwarven Toughness) | 23 → 32 | 17 → 24 |
| CA | 14 (Mage Armor) | 14 (Chain Shirt + escudo) | 13 (Unarmored Defense) | 15 (Unarmored Defense) |
| Deslocamento | 30 | 30 | 35 | 40 (Unarmored Movement) |
| Recursos no nível 2 → 3 | espaços 3 → 4+2 | espaços 3 → 4+2; Channel Divinity 2 | Fúria 2 → 3 | Foco 2 → 3 |

**Nível 3, aplicado pelos dados:**

- **Mago → Evoker.**
  - *Evocation Savant* acrescenta Scorching Ray e Flaming Sphere ao grimório. Flaming
    Sphere conta como evocação pela D-003.
  - O grimório vai de 8 para 12 magias (+2 por nível, mais as 2 gratuitas).
  - Magias preparadas: 6; entra Scorching Ray.
  - *Potent Cantrip* passa a funcionar.
  - Detect Magic fica sempre preparada (Alto Elfo, nível 3).
- **Clériga → Life Domain.**
  - *Disciple of Life* e *Preserve Life*.
  - Aid, Bless, Cure Wounds e Lesser Restoration ficam sempre preparadas, fora do limite
    de 6.
- **Bárbaro → Path of the Berserker.**
  - *Frenzy*.
  - *Primal Knowledge*: escolheu Nature.
  - Fúrias: 3.
- **Monge → Warrior of the Open Hand.**
  - *Open Hand Technique*.
  - *Deflect Attacks*.
  - Pontos de Foco: 3.

## 3. Os combates (semente 2026)

**Combate 1 (nível 2, 3 rodadas, vitória sem baixas).**

- Rodada 1:
  - o Bárbaro entra em Fúria;
  - o Ataque Imprudente dá vantagem, e Fire's Burn soma 1d10 de fogo no acerto;
  - o Mago lança Sleep: um goblin falha, fica Incapacitated, e no fim do turno dele falha
    de novo e cai Unconscious e Prone;
  - o Mago usa Shield (reação) contra as flechas: a CA vai a 19;
  - a Clériga lança Bless, com concentração.
- Rodada 2:
  - o Monge ataca com a lança (Destreza, por Martial Arts) e usa Flurry of Blows;
  - o golpe desarmado também usa Destreza;
  - o Bárbaro acerta o goblin adormecido: crítico automático (Unconscious a até 1,5 m);
    o dano acorda o goblin e o mata;
  - Guiding Bolt.
- Rodada 3: o Monge e o Fire Bolt crítico do Mago derrubam os últimos.

**Depois do combate:**
- XP: 6 × 50 = 300, ou seja 75 por personagem. Total de 375, abaixo dos 900 do nível 3.
- Descanso Curto: Hit Point Dice gastos; Arcane Recovery limitado ao nível 5; Fúria +1;
  Channel Divinity +1; Foco completo.
- Nível 3 e Descanso Longo.

**Combate 2 (nível 3, 4 rodadas, vitória).**
- O Mago cai a 0 PV com um crítico e perde a concentração em Sleep.
- A Clériga usa Healing Word (+3 de *Disciple of Life*) e Divine Spark.
- O Mago volta, levanta-se (*Right yourself*, metade do deslocamento) e lança Scorching Ray.
- Em outras sementes aparecem também:
  - *Frenzy*: Fúria + Imprudente;
  - *Open Hand Technique*: Topple deixando Prone;
  - *Deflect Attacks* zerando o dano;
  - *Vex* e *Cleave*;
  - *Potent Cantrip*;
  - salvaguardas contra a morte.

**200 sementes (antes → depois das correções):**

| | Antes | Depois |
|---|---|---|
| Vitórias no combate 1 / 2 | 198 / 200 | 200 / 200 |
| Rodadas médias (1 / 2) | 5,0 / 3,89 | 4,76 / 3,69 |
| Quedas a 0 PV (1 / 2) | 204 / 40 | 162 / 24 |
| Mortes de personagem | 9 | 2 |

Antes, a Fúria não ficava ativa: a resistência e o dano extra nunca valiam, e o Bárbaro
gastava uma Fúria por turno. Sleep aplicava as duas salvaguardas de uma vez. Por isso o grupo
sofria mais.

## 4. Chamadas por fase (semente narrada)

| Fase | OK | DATA_GAP | ENGINE_GAP | GM |
|---|---|---|---|---|
| 1. Criação e nível 2 | 242 | 0 | 0 | 0 |
| 2. Combate no nível 2 | 403 | 0 | 0 | 0 |
| 3. XP e Descanso Curto | 13 | 0 | 0 | 1 |
| 4. Nível 3 | 189 | 0 | 0 | 0 |
| 5. Combate no nível 3 | 655 | 0 | 0 | 0 |

A única chamada `GM` é a premissa do exercício. O motor calcula 375 XP e não 900, então
o nível 3 vem por decisão do mestre. As regras de XP do SRD estão aplicadas; a subida por
marco não está no SRD, e por isso não foi acrescentada.

## 5. O que estava quebrado e foi corrigido (46 tipos de chamada)

| Lacuna encontrada | Correção (D-005) |
|---|---|
| CD de magia, bônus de ataque mágico e CA base: fórmulas existiam em `levels.rules`, mas o motor não tinha caminho até elas | `registries.<nome>.formula` |
| Ataque usa Força (corpo a corpo) ou Destreza (distância): tabela só em texto | o motor lê as fórmulas `melee/ranged_attack_bonus` |
| PV por nível: células de tabela "7 + Con. modifier" | `class.data.hit_points` (expressões) |
| Equipamento inicial de classe e de antecedente: `reference` para a própria entrada com nota | `grant {items, gp}` |
| Aumento de atributos do antecedente só como dado de regra | `choice` com as 7 combinações |
| Subclasse concedia todas as características de uma vez | `grant` por nível com `level_at_least` |
| Fúria: ativação apontava para si mesma, então "Fúria ativa" nunca valia | `activation.duration` |
| Golpe Desarmado: Dano/Agarrar/Empurrar lado a lado, e bônus fixo em Força | `choice`; `attack_ability_mod` |
| Nimble Escape: Disengage **e** Hide | `choice` (também Cunning Action e outros 7 monstros) |
| Sleep: 2ª salvaguarda imediata (o momento estava na nota) | `trigger` no fim do próximo turno do alvo + `ends_on` dano |
| Inconsciente a 0 PV "até recuperar PV" só na nota | `while: hp_is {zero}` |
| Incapacitated implícito em 4 condições só na nota | `while: has_condition` |
| Guiding Bolt e Vex: "só a próxima jogada" na nota | `ends_on: targeted_by_attack_roll`, `roller_is_source` |
| Cleave e Light: "sem modificador no dano" na nota | `ability_modifier_to_damage` |
| Arcane Recovery e Natural Recovery: "nenhum de nível 6+" na nota | `restore.max_level` |
| Magic Initiate: nível das magias só na nota; `cast_spell` apontava para o talento | `grant.filter`, `chosen.level_1_spell` |
| Linhagens de elfo e legados de tiefling: placeholders | efeitos da tabela, com magias nos níveis 3 e 5 |
| Ferramentas do Monge/Bardo/Druida/Ladino e Human Skillful só em nota | `items` / `from` |
| `holy_symbol` não era slug do catálogo | `holy-symbol` |

## 6. O que ainda falta para o motor de produção

`tools/validate/engine_contract.py` (relatório em `reports/engine_contract.json`) confronta
o catálogo inteiro com o protótipo. Esses itens não aparecem no encontro com goblins, mas
aparecerão em outros:

- **Entradas com efeitos totalmente executáveis pelo protótipo:** 869 de 1.391.
- **Ops ainda não executadas:**
  - `cast_spell`, em 154 entradas (itens mágicos e conjuração inata);
  - `summon` (23);
  - `transform` (5);
  - `sense` (35), que é lido, mas não há modelo de visão.
- **Predicados e variáveis:**
  - 111 dos 145 predicados usados não têm implementação no protótipo; por exemplo
    `target_size_at_most` (42) e `creature_is` (25);
  - 29 das 44 variáveis, por exemplo `charges_spent` e `spell_level`.
- **Campos ainda não lidos:**
  - `activation.frequency` (104);
  - `apply_condition.params` (50);
  - `save.repeat` (31);
  - `defense.conditions` (17);
  - os campos de `summon`.
- **351 notas para revisar.** Elas contêm palavras como *only*, *next*, *until*, *half* e
  *at the end*. Nesta simulação, 5 das 18 notas encontradas escondiam mecânica (seção 5);
  a mesma proporção pode existir no resto do catálogo.
EOF
echo ok