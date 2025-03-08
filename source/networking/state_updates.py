from ursina import time
from ursina.networking import rpc

from . import network

from ..states.cbstate_complete import CompleteCombatState, apply_complete_cb_state
from ..states.cbstate_mini import MiniCombatState, apply_mini_state
from ..states.physicalstate import PhysicalState


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
