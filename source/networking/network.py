from ursina import *
from ursina.networking import RPCPeer, rpc

from ..gamestate import gs
from ..states import State

UPDATE_RATE = 1 / 20

class Network(Entity):
    """Represents a peer's interface into the network state"""
    def __init__(self):
        super().__init__()
        self.peer = RPCPeer(max_list_length=100)

        self.uuid_to_char = dict()
        self.connection_to_char = dict()
        self.uuid_to_connection = dict()

        self.server_connection = None

        # uuid is more like a unique character id, npc's get them too
        self.uuid_counter = 0
        self.my_uuid = None

        self.inst_id_to_item = dict()
        self.item_inst_id_ct = 0
        self.inst_id_to_power = dict()
        self.power_inst_id_ct = 0
        self.inst_id_to_container = dict()
        self.container_inst_id_ct = 0

    @every(UPDATE_RATE)
    def fixed_update(self):
        network.peer.update()

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
