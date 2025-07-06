from ursina import Ursina
from ursina.networking import rpc

from source.gamestate import gs
from source.network import network
from source.disconnect import *
from source.server.world_requests import *
from source.server.world_gen import ServerWorld

def start_server(name, port):
    network.peer.start(name, port, is_host=True)
    network.my_uuid = network.uuid_counter
    network.uuid_counter += 1
    gs.world = ServerWorld("demo.json")
    npcs = gs.world.create_npcs("demo_npcs.json")
    gs.chars += npcs
    for npc in npcs:
        npc.controller = MobController(npc)
        npc.uuid = network.uuid_counter
        network.uuid_to_char[npc.uuid] = npc
        network.uuid_counter += 1


if __name__ == "__main__":
    # app = Ursina(window_type="offscreen")
    app = Ursina(window_type="none")
    start_server("localhost", 8080)
    app.run()
    
