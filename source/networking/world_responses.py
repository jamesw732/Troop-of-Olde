"""These are generic RPC functions that are only called by the host"""
from ursina.networking import rpc

from . import network
from ..item import *

@rpc(network.peer)
def toggle_combat(connection, time_received, toggle: bool):
    my_char = network.uuid_to_char.get(network.my_uuid)
    my_char.in_combat = toggle
    msg = "Now entering combat" if toggle else "Now leaving combat"
    ui.gamewindow.add_message(msg)

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell other peers that a character died. Only to be called by host.
    Move this."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()


@rpc(network.peer)
def remote_update_container(connection, time_received, container_name: str, container: IdContainer):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    if network.peer.is_hosting():
        return
    internal_container = ids_to_container(container)
    update_container(container_name, internal_container)

