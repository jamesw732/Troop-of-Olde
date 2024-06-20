"""Contains basic networking definitions, free to be accessed by any module"""
from ursina import *
from ursina.networking import *


class Network:
    def __init__(self):
        self.peer = RPCPeer()

        self.uuid_to_char = dict()
        self.connection_to_char = dict()


        # uuid is more like a unique character id, npc's get them too
        self.uuid_counter = 0
        self.my_uuid = None

        self.pc = None
        self.world = None
        self.chars = []
        self.npcs = []

        self.update_rate = 0.2
        self.update_timer = 0.0

network = Network()

@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    print(msg)

def broadcast(func, *args):
    """Calls an RPC function for each connection to host"""
    if network.peer.is_hosting():
        for connection in network.peer.get_connections():
            func(connection, *args)