"""Defines and declares the network state. Also some universally helpful
networking methods. Any file that uses networking will import this."""
from ursina import *
from ursina.networking import *


class Network:
    """Represent's client's view of the network state"""
    def __init__(self):
        self.peer = RPCPeer()

        self.uuid_to_char = dict()
        self.connection_to_char = dict()

        # uuid is more like a unique character id, npc's get them too
        self.uuid_counter = 0
        self.my_uuid = None

        self.update_rate = 0.2
        self.update_timer = 0.0

# RPC needs to know about network at compile time, so this global seems necessary
network = Network()

@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    print(msg)

def broadcast(func, *args):
    """Calls an RPC function for each connection to host
    func: an RPC function
    args: arguments to the RPC function besides connection"""
    if network.peer.is_hosting():
        for connection in network.peer.get_connections():
            func(connection, *args)

def is_main_client():
    """Returns whether client is host, or single player"""
    return network.peer.is_hosting() or not network.peer.is_running()