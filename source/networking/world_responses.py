"""These are generic RPC functions that are only called by the host.

These will typically only be called by functions in world_requests as part
of a response to a request. Otherwise, they may be called by host_continuous."""
from ursina.networking import rpc

from .network import network
from ..item import *
from ..ui.base import ui
from ..gamestate import gs
from ..states.state import State, apply_physical_state, apply_state

# Combat
@rpc(network.peer)
def toggle_combat(connection, time_received, toggle: bool):
    my_char = network.uuid_to_char.get(network.my_uuid)
    my_char.in_combat = toggle
    msg = "Now entering combat" if toggle else "Now leaving combat"
    ui.gamewindow.add_message(msg)

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell clients that a character died. Only to be called by host."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()

@rpc(network.peer)
def remote_set_target(connection, time_received, uuid: int):
    """Update player character's target"""
    tgt = network.uuid_to_char[uuid]
    gs.pc.target = tgt
    msg = f"Now targeting: {tgt.cname}"
    ui.gamewindow.add_message(msg)

@rpc(network.peer)
def update_pc_cbstate(connection, time_received, uuid: int, cbstate: State):
    """Update combat state for a player character"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_state(char, cbstate)

@rpc(network.peer)
def update_npc_cbstate(connection, time_received, uuid: int, cbstate: State):
    """Update combat state for an NPC"""
    char = network.uuid_to_char.get(uuid)
    if char:
        apply_state(char, cbstate)

# Items
@rpc(network.peer)
def remote_update_container(connection, time_received, container_name: str, container: IdContainer):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    if network.peer.is_hosting():
        return
    internal_container = ids_to_container(container)

    loop = internal_container.items()
    container = getattr(gs.pc, container_name)
    for slot, item in loop:
        container[slot] = item
        auto_set_primary_option(item, container_name)

    ui.playerwindow.items.update_ui_icons(container_name, loop=loop)
    # Should probably also force update player stats now

# Physical
@rpc(network.peer)
def update_lerp_pstate(connection, time_received, uuid: int,
                       phys_state: State):
    """Remotely call char.update_lerp_state"""
    npc = network.uuid_to_char.get(uuid)
    if npc is None:
        return
    npc.update_lerp_state(phys_state, time_received)

# Generic
@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    ui.gamewindow.add_message(msg)
