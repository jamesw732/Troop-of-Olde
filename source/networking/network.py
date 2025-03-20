from ursina.networking import RPCPeer, rpc

from ..gamestate import gs

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
        func: an RPC function
        args: arguments to the RPC function besides connection"""
        if self.peer.is_hosting():
            for connection in network.peer.get_connections():
                func(connection, *args)


# RPC needs to know about network at compile time, so this global seems necessary
network = Network()
gs.network = network
