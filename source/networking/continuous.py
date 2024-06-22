from ursina import *
from ursina.networking import *

from .base import *
from ..physics import PhysicalState
from ..combat import CombatState

from ..gamestate import *


# CODE FOR CONTINUOUS UPDATES
def update():
    network.peer.update()
    # No point updating if no peers
    if not (network.peer.is_running() and network.peer.connection_count() > 0):
        return
    my_char = network.uuid_to_char.get(network.my_uuid)
    if not my_char:
        return

    network.update_timer += time.dt
    if network.update_timer >= network.update_rate:
        network.update_timer -= network.update_rate
        new_state = my_char.get_physical_state()
        connections = network.peer.get_connections()
        for connection in connections:
            network.peer.update_char_pstate(connection, my_char.uuid, new_state)
        if network.peer.is_hosting():
            for char in gs.chars:
                cbstate = char.get_combat_state()
                for connection in connections:
                    network.peer.update_char_cstate(connection, char.uuid, cbstate)


@rpc(network.peer)
def update_char_pstate(connection, time_received, uuid: int,
                       phys_state: PhysicalState):
    """Mostly the RPC wrapper for Character.apply_physical_state, eventually
    Character.update_lerp_state.
    Character state is client-authoritative, so when host receives this, it
    recursively calls it again for each other connection.
    """
    char = network.uuid_to_char.get(uuid)
    if char:
        char.update_lerp_state(phys_state, time_received)
    if network.peer.is_hosting():
        state = char.get_physical_state()
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_char_pstate(conn, state)

@rpc(network.peer)
def update_char_cstate(connection, time_received, uuid: int, cbstate: CombatState):
    char = network.uuid_to_char.get(uuid)
    if char:
        char.apply_combat_state(cbstate)