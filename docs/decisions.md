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

**Extensão (mesmo princípio, a confirmar):** *Flaming Sphere* (p. 132) aparece como
Conjuration na descrição e como Evocation nas listas de Druid, Sorcerer e Wizard. A
descrição é tratada como autoritativa também para a escola (Conjuration); as listas
registram a divergência.

Aplicada por: `tools/inventory/build_inventory.py` (campo `resolution`) e pelo lote L27.

## D-002 — Idioma

Os arquivos de dados ficam em inglês, como a fonte. Uma camada de tradução pt-BR será
criada depois, em arquivo separado, sem alterar as entradas.
