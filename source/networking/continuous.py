from ursina import time
from ursina.networking import rpc

from . import network

from ..gamestate import gs
from ..states.cbstate_complete import CompleteCombatState, apply_complete_cb_state
from ..states.cbstate_mini import MiniCombatState, apply_mini_state
from ..states.physicalstate import PhysicalState


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
        new_state = PhysicalState(my_char)
        connections = network.peer.get_connections()
        for connection in connections:
            network.peer.update_char_pstate(connection, my_char.uuid, new_state)
        if network.peer.is_hosting():
            for char in gs.chars:
                mini_state = MiniCombatState(char)
                for connection in connections:
                    if connection not in network.connection_to_char:
                        continue
                    if network.connection_to_char[connection] is char:
                        network.peer.update_pc_cbstate(connection, char.uuid,
                                                       CompleteCombatState(char))
                    else:
                        network.peer.update_npc_cbstate(connection, char.uuid,
                                                        mini_state)


@rpc(network.peer)
def update_char_pstate(connection, time_received, uuid: int,
                       phys_state: PhysicalState):
    """Client-authoritatively apply physical state updates.
    Don't apply new state directly, instead add it as the new LERP state.
    Host will broadcast the new state to all other peers.
    """
    char = network.uuid_to_char.get(uuid)
    if char:
        char.update_lerp_state(phys_state, time_received)
    if network.peer.is_hosting():
        state = PhysicalState(char)
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_char_pstate(conn, uuid, state)

@rpc(network.peer)
def update_pc_cbstate(connection, time_received, uuid: int, cbstate: CompleteCombatState):
    """Update state for somebody else's player character"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_complete_cb_state(char, cbstate)

@rpc(network.peer)
def update_npc_cbstate(connection, time_received, uuid: int, cbstate: MiniCombatState):
    """Update state for character that the client doesn't care about very much"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_mini_state(char, cbstate)