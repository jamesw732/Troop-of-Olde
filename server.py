from ursina import Ursina
from ursina.networking import rpc

from source.network import network
from source.disconnect import *
from source.server.world_requests import *
from source.server.world import world

def start_server(name, port):
    network.peer.start(name, port, is_host=True)
    world.load_zone("demo.json")
    world.load_npcs("demo_npcs.json")


if __name__ == "__main__":
    # app = Ursina(window_type="offscreen")
    app = Ursina(window_type="none")
    start_server("localhost", 8080)
    app.run()
    
