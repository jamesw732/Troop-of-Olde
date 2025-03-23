from ursina.networking import RPCPeer, rpc

from ..gamestate import gs
from ..states import State

class Network:
    """Represents a peer's interface into the network state"""
    def __init__(self):
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

        self.update_rate = 0.2
        self.update_timer = 0.0

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
        connections = network.peer.get_connections()
        for connection in connections:
            if connection not in network.connection_to_char:
                continue
            if network.connection_to_char[connection] is char:
                network.peer.update_pc_cbstate(connection, char.uuid, pc_state)
                # gs.ui.update_bars()
            else:
                network.peer.update_npc_cbstate(connection, char.uuid, npc_state)


# RPC needs to know about network at compile time, so this global seems necessary
network = Network()
gs.network = network
