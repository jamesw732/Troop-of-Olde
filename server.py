from ursina import Ursina
from ursina.networking import rpc

from source.gamestate import gs
from source.networking import network
from source.networking.connect import *
from source.networking.continuous import *
from source.networking.disconnect import *
from source.networking.register import *
from source.npc_controller import NPC_Controller
from source.world_gen import GenerateWorld

def start_server(name, port):
    network.peer.start(name, port, is_host=True)
    network.my_uuid = network.uuid_counter
    network.uuid_counter += 1
    gs.world = GenerateWorld("demo.json", headless=True)
    npcs = gs.world.create_npcs("demo_npcs.json")
    gs.chars += npcs
    for npc in npcs:
        npc.controller = NPC_Controller(npc)
        npc.uuid = network.uuid_counter
        network.uuid_to_char[npc.uuid] = npc
        network.uuid_counter += 1


if __name__ == "__main__":
    # app = Ursina(window_type="offscreen")
    app = Ursina(window_type="none")
    start_server("localhost", 8080)
    app.run()
    
