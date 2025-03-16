from ursina import time
from ursina.networking import rpc

from . import network

from ..states.cbstate_complete import CompleteCombatState, apply_complete_cb_state
from ..states.cbstate_mini import MiniCombatState, apply_mini_state
from ..states.physicalstate import PhysicalState, apply_physical_state


@rpc(network.peer)
def update_char_pstate(connection, time_received, uuid: int,
                       phys_state: PhysicalState):
    """Client-authoritatively apply physical state updates.
    Don't apply new state directly, instead add it as the new LERP state.
    Host will broadcast the new state to all other peers.
    """
    char = network.uuid_to_char.get(uuid, None)
    if char is None:
        return
    apply_physical_state(char, phys_state)
    if network.peer.is_hosting():
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_lerp_pstath(conn, uuid, phys_state)

@rpc(network.peer)
def update_lerp_pstate(connection, time_received, uuid: int,
                       phys_state: PhysicalState):
    char = network.uuid_to_char.get(uuid)
    if char is None:
        return
    char.update_lerp_state(phys_state, time_received)

@rpc(network.peer)
def update_pc_cbstate(connection, time_received, uuid: int, cbstate: CompleteCombatState):
    """Update combat state for a player character"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_complete_cb_state(char, cbstate)

@rpc(network.peer)
def update_npc_cbstate(connection, time_received, uuid: int, cbstate: MiniCombatState):
    """Update combat state for an NPC"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_mini_state(char, cbstate)
