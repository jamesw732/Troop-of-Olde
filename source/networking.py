from ursina import *
from ursina.networking import *
import os

from .character import Character, CharacterState
from .mob import Mob, MobState
from .npc_controller import *
from .player_controller import PlayerController
from .world_gen import *

uuid_to_char = dict()
connection_to_char = dict()

chars = []

# uuid is more like a unique character id, npc's get them too
uuid_counter = 0
my_uuid = None

update_rate = 0.2
update_timer = 0.0


peer = RPCPeer()

peer.register_type(CharacterState, serialize_character_state,
                   deserialize_character_state)
peer.register_type(MobState, serialize_mob_state, deserialize_mob_state)

pc = None
world = None
npcs = []
npc_controllers = []


def update():
    peer.update()

    for char in chars:
        if my_uuid is not None:
            char.rotate_namelabel(uuid_to_char[my_uuid].position
                - camera.world_position)

    global update_timer
    update_timer += time.dt
    if update_timer >= update_rate:
        update_timer -= update_rate
        if peer.is_running() and peer.connection_count() > 0:
            new_state = uuid_to_char[my_uuid].get_state()
            for connection in peer.get_connections():
                peer.update_char_state(connection, new_state)


# Login handling
def input(key):
    if not peer.is_running():
        if key == "h":
            global pc, world, chars, npcs, npc_controllers, uuid_counter, my_uuid
            char = Character("Player", speed=20.0, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
            my_uuid = uuid_counter
            uuid_counter += 1
            char.uuid = my_uuid
            uuid_to_char[my_uuid] = char
            chars.append(char)
            char.ignore_traverse = chars
            pc = PlayerController(char, peer=peer)

            world = GenerateWorld("data/zones/demo.json")
            npcs = world.create_npcs("data/zones/demo_npcs.json")
            chars += npcs
            for npc in npcs:
                npc.controller = NPC_Controller(npc, char)
                npc.uuid = uuid_counter
                uuid_to_char[npc.uuid] = npc
                uuid_counter += 1

            peer.start("localhost", 8080, is_host=True)
        elif key == "c":
            print("Attempting to connect")
            peer.start("localhost", 8080, is_host=False)

# CONNECTION FUNCTIONS
@rpc(peer)
def on_connect(connection, time_connected):
    """What host should do when there's a new connection
    Host just needs to make a new character, map connection/uuid to it, increment uuid,
    and send the new character to peers.
    Will need to generate world on peer, spawn all characters including
    peer's + make mob/bind to character, and bind peer's character to my_uuid.
    Eventually, this will not be done on connection, it will be done on "enter world"."""
    global uuid_counter
    if peer.is_hosting():
        char = Character(name="Player", speed=20.0, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
        char.uuid = uuid_counter
        uuid_to_char[char.uuid] = char
        uuid_counter += 1
        chars.append(char)
        connection_to_char[connection] = char
        new_state = char.get_state()
        peer.generate_world(connection, "data/zones/demo.json")
        states = [c.get_state() for c in chars]
        for conn in peer.get_connections():
            if conn == connection:
                for state in states:
                    peer.spawn_character(conn, state)
            else:
                peer.spawn_character(conn, new_state)
        peer.bind_uuid_to_char(connection, char.uuid)

@rpc(peer)
def generate_world(connection, time_received, zone:str):
    source = os.path.abspath(os.path.dirname(__file__))
    zonepath = os.path.join(source, "..", zone)
    GenerateWorld(zonepath)

@rpc(peer)
def spawn_character(connection, time_received, char_state:CharacterState):
    # add mob_state parameter to this soon
    if peer.is_hosting():
        return
    if char_state.uuid not in uuid_to_char:
        char = Character(state=char_state)
        chars.append(char)
        uuid_to_char[char_state.uuid] = char

@rpc(peer)
def bind_uuid_to_char(connection, time_received, uuid:int):
    if peer.is_hosting():
        return
    global my_uuid, pc
    my_uuid = uuid
    chars[my_uuid].ignore_traverse = chars
    pc = PlayerController(uuid_to_char[uuid], peer)
    pc.character = uuid_to_char[uuid]

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
def update_char_state(connection, time_received, char_state: CharacterState):
    """Mostly the RPC wrapper for Character.apply_state, eventually
    Character.update_lerp_state.
    Character state is client-authoritative, so when host receives this, it
    recursively calls it again for each other connection.
    """
    char = uuid_to_char.get(char_state.uuid)
    if char is not None:
        char.apply_state(char_state)
    if peer.is_hosting():
        state = char.get_state()
        for conn in peer.get_connections():
            if conn is not connection:
                peer.update_char_state(conn, state)

@rpc(peer)
def update_mob_state(connection, time_received, mob_state: MobState):
    """Mostly the RPC wrapper for Mob.apply_state.
    Mob state is server-authoritative, so host will be the only peer to ever call this."""
    pass

# SINGULAR UPDATE FUNCTIONS

@rpc(peer)
def attempt_attack_remote(connection, time_received, srcuuid: int, tgtuuid: int):
    """Called by non-hosts, wrapper for Mob.attempt_attack which guarantees combat is
    synchronized."""
    pass