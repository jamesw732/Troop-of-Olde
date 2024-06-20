from .base import *
from ..character import CharacterState

from ..world_defns import *


# CODE FOR CONTINUOUS UPDATES
def update():
    network.peer.update()
    my_char = network.uuid_to_char.get(network.my_uuid)
    if not my_char:
        return
    for char in chars:
        if network.my_uuid is not None:
            char.rotate_namelabel(my_char.position - camera.world_position)

    network.update_timer += time.dt
    if network.update_timer >= network.update_rate:
        network.update_timer -= network.update_rate
        if network.peer.is_running() and network.peer.connection_count() > 0:
            new_state = my_char.get_state()
            for connection in network.peer.get_connections():
                network.peer.update_char_state(connection, new_state)

@rpc(network.peer)
def update_char_state(connection, time_received, char_state: CharacterState):
    """Mostly the RPC wrapper for Character.apply_state, eventually
    Character.update_lerp_state.
    Character state is client-authoritative, so when host receives this, it
    recursively calls it again for each other connection.
    """
    char = network.uuid_to_char.get(char_state.uuid)
    if char:
        char.apply_state(char_state)
    if network.peer.is_hosting():
        state = char.get_state()
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_char_state(conn, state)