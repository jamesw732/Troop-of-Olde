from ursina import *

from source.character import *
from source.player_controller import *
from source.npc_controller import *
from source.world_gen import *
from source.gamestate import *
from source.item import *
from source.ui.main import ui
from source.states.cbstate_base import BaseCombatState

app = Ursina(borderless=False)
gs.world = GenerateWorld("demo.json")

pstate = PhysicalState(position=Vec3(0, 1, 0))
basestate = BaseCombatState(haste=1000, bdy=100)
sword = Item("1")
sword2 = Item("2")
sword3 = Item("2")

player = Character(pstate=pstate, base_state=basestate,
                   equipment={"mh": sword, "oh": sword3}, inventory=[sword2])
player.ignore_traverse = gs.chars
gs.pc = PlayerController(player)

npcs = gs.world.create_npcs("demo_npcs.json")
for npc in npcs:
    npc.controller = NPC_Controller(npc, player)

gs.chars += npcs
gs.chars.append(player)

ui.make()

app.run()