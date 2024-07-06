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

pname = "Demo Player"
player = load_character_from_json(pname)
player.ignore_traverse = gs.chars
gs.pc = player
gs.playercontroller = PlayerController(player)

npcs = gs.world.create_npcs("demo_npcs.json")
for npc in npcs:
    npc.controller = NPC_Controller(npc, player)

gs.chars += npcs
gs.chars.append(player)

ui.make()

app.run()