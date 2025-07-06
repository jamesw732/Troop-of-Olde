from ursina import *
from ursina.networking import RPCPeer, rpc

from .gamestate import gs
from .states import *

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
        self.peer.update()

    def broadcast(self, func, *args):
        """Calls an RPC function for each connection to host
        func: an RPC function, include network.peer
        args: arguments to the RPC function besides connection"""
        if self.peer.is_hosting():
            for connection in self.peer.get_connections():
                func(connection, *args)

    def container_to_ids(self, container, id_type="inst_id"):
        """Convert a container (Character attribute) to one sendable over the network

        container: list containing Items
        id_type: the literal id attribute of the item, or tuple of id attributes
        In the latter case, returns a 1d list stacked in order of the id attributes"""
        if isinstance(id_type, tuple):
            return [getattr(item, id_subtype) if hasattr(item, id_subtype) else -1 for id_subtype in id_type
                    for item in container]
        return [getattr(item, id_type) if hasattr(item, id_type) else -1 for item in container]


    def ids_to_container(self, id_container):
        """Convert container of inst ids to a list of objects"""
        return [self.inst_id_to_item.get(itemid, None) for itemid in id_container]

    def broadcast_cbstate_update(self, char):
        pc_state = PlayerCombatState(char)
        npc_state = NPCCombatState(char)
        connections = self.connection_to_char
        for connection in connections:
            if self.connection_to_char[connection] is char:
                self.peer.update_pc_cbstate(connection, char.uuid, pc_state)
            else:
                self.peer.update_npc_cbstate(connection, char.uuid, npc_state)


# RPC needs to know about network at compile time, so this global seems necessary
network = Network()
gs.network = network

network.peer.register_type(BaseCombatState, BaseCombatState.serialize, BaseCombatState.deserialize)
network.peer.register_type(SkillsState, SkillsState.serialize, SkillsState.deserialize)
network.peer.register_type(PlayerCombatState, PlayerCombatState.serialize, PlayerCombatState.deserialize)
network.peer.register_type(NPCCombatState, NPCCombatState.serialize, NPCCombatState.deserialize)
network.peer.register_type(PhysicalState, PhysicalState.serialize, PhysicalState.deserialize)
network.peer.register_type(Stats, Stats.serialize, Stats.deserialize)
