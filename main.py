from ursina import *

from source.character import *
from source.player_controller import *
from source.npc_controller import *
from source.world_gen import *
from source.gamestate import *
from source.ui.main import ui

app = Ursina(borderless=False)
gs.world = GenerateWorld("demo.json")

pstate = PhysicalState(position=(0, 1, 0))
cbstate = CombatState(health=100, speed=20, str=10, dex=10, haste=1000)

player = Character(pstate=pstate, cbstate=cbstate)
player.ignore_traverse = gs.chars
gs.pc = PlayerController(player)

npcs = gs.world.create_npcs("demo_npcs.json")
for npc in npcs:
    npc.controller = NPC_Controller(npc, player)

gs.chars += npcs
gs.chars.append(player)

ui.make()

app.run()