from ursina import *
from ursina.networking import RPCPeer, rpc

from ..gamestate import gs
from ..states import State

UPDATE_RATE = 1 / 20

class Network(Entity):
    """Represents a peer's interface into the network state"""
    def __init__(self):
        super().__init__()
        self.peer = RPCPeer()

        self.uuid_to_char = dict()
        self.connection_to_char = dict()
        self.uuid_to_connection = dict()
        self.iiid_to_item = dict()

        self.server_connection = None

        # uuid is more like a unique character id, npc's get them too
        self.uuid_counter = 0
        self.my_uuid = None

        self.iiid_counter = 0


    @every(UPDATE_RATE)
    def fixed_update(self):
        network.peer.update()
        if not self.peer.is_hosting():
            my_char = network.uuid_to_char.get(network.my_uuid)
            if my_char is None:
                return
            new_state = State("physical", my_char)
            for conn in network.peer.get_connections():
                self.peer.request_update_pstate(conn, self.my_uuid, new_state)


    def broadcast(self, func, *args):
        """Calls an RPC function for each connection to host
        func: an RPC function, include network.peer
        args: arguments to the RPC function besides connection"""
        if self.peer.is_hosting():
            for connection in self.peer.get_connections():
                func(connection, *args)

    def broadcast_cbstate_update(self, char):
        pc_state = State("pc_combat", char)
        npc_state = State("npc_combat", char)
        connections = network.connection_to_char
        for connection in connections:
            if network.connection_to_char[connection] is char:
                network.peer.update_cbstate(connection, char.uuid, pc_state)
            else:
                network.peer.update_cbstate(connection, char.uuid, npc_state)


# RPC needs to know about network at compile time, so this global seems necessary
network = Network()
gs.network = network
