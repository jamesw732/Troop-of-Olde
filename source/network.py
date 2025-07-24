from ursina import *
from ursina.networking import RPCPeer, rpc

from .states import *

UPDATE_RATE = 1 / 20

class Network(Entity):
    """Represents a peer's interface into the network state"""
    def __init__(self):
        super().__init__()
        self.peer = RPCPeer(max_list_length=1000)

        self.connection_to_uuid = dict()
        self.uuid_to_connection = dict()

        self.server_connection = None
        self.my_uuid = None

        self.peer.register_type(LoginState, LoginState.serialize, LoginState.deserialize)
        self.peer.register_type(PCSpawnState, PCSpawnState.serialize, PCSpawnState.deserialize)
        self.peer.register_type(NPCSpawnState, NPCSpawnState.serialize, NPCSpawnState.deserialize)
        self.peer.register_type(PlayerCombatState, PlayerCombatState.serialize, PlayerCombatState.deserialize)
        self.peer.register_type(NPCCombatState, NPCCombatState.serialize, NPCCombatState.deserialize)
        self.peer.register_type(Stats, Stats.serialize, Stats.deserialize)

    @every(UPDATE_RATE)
    def fixed_update(self):
        self.peer.update()

    def broadcast(self, func, *args):
        """Calls an RPC function for each connection to host
        func: an RPC function, include network.peer
        args: arguments to the RPC function besides connection"""
        if self.peer.is_hosting():
            for connection in self.peer.get_connections():
                func(connection, *args)

    def broadcast_cbstate_update(self, char):
        pc_state = PlayerCombatState(char)
        npc_state = NPCCombatState(char)
        for connection, uuid in self.connection_to_uuid.items():
            if uuid == char.uuid:
                self.peer.update_pc_cbstate(connection, uuid, pc_state)
            else:
                self.peer.update_npc_cbstate(connection, uuid, npc_state)


# RPC needs to know about network at compile time, so this global seems necessary
network = Network()
