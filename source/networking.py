from ursina.networking import *
from player_controller import PlayerController

from .character import Character, CharacterState
from .mob import Mob, MobState

uuid_to_char = dict()
connection_to_char = dict()

chars = []

uuid_counter = 0
my_uuid = None

update_rate = 0.2
update_timer = 0.0


peer = RPCPeer()
pc = PlayerController(peer)

# CONNECTION FUNCTIONS
@rpc(peer)
def on_connect(connection, time_connected):
    """What host should do when there's a new connection
    Host just needs to make a new character, map connection/uuid to it, increment uuid,
    and send the new character to peers.
    Will need to generate world on peer, spawn all characters including
    peer's + make mob/bind to character, and bind peer's character to my_uuid.
    Eventually, this will not be done on connection, it will be done on "enter world"."""
    pass

@rpc(peer)
def generate_world(connection, time_received, zone:str):
    pass

@rpc(peer)
def spawn_character(connection, time_received, char:CharacterState, mob: MobState):
    pass

@rpc(peer)
def bind_uuid_to_char(connection, time_received, uuid):
    pass

# DISCONNECTION FUNCTIONS
@rpc(peer)
def on_disconnect(connection, time_received):
    """What other clients should do when you disconnect
    When host receives this call, delete all references to character, and
    tell clients to delete those references as well.
    When a non-host receives this call, it means the host disconnected. In this case,
    delete all characters. Eventually, save character state too"""
    pass

@rpc(peer)
def remote_remove_char(connection, time_received, uuid: int):
    """What a non-host does to remove a character"""
    pass

def remove_char(uuid:int):
    """Helper function for removing a box.
    Whether to remove reference in connection_to_char depends on peer.is_hosting()"""
    pass

# CONTINUOUS UPDATE FUNCTIONS
@rpc(peer)
def update_char_state(connection, time_received, charstate: CharacterState):
    """Mostly the RPC wrapper for Character.apply_state, eventually
    Character.update_lerp_state.
    Character state is client-authoritative, so when host receives this, it
    recursively calls it again for each other connection.
    """
    pass

@rpc(peer)
def update_mob_state(connection, time_received, mobstate: MobState):
    """Mostly the RPC wrapper for Mob.apply_state.
    Mob state is server-authoritative, so host will be the only peer to ever call this."""
    pass

# SINGULAR UPDATE FUNCTIONS

@rpc(peer)
def attempt_attack_remote(connection, time_received, srcuuid: int, tgtuuid: int):
    """Called by non-hosts, wrapper for Mob.attempt_attack which guarantees combat is
    synchronized."""
    pass