"""Clients are currently responsible for sharing their physical location/rotation/etc with all peers"""
from ursina import time
from ursina.networking import rpc

from . import network
from .world_requests import *
from ..states.physicalstate import PhysicalState


def update():
    network.peer.update()
    my_char = network.uuid_to_char.get(network.my_uuid)

    if my_char is None:
        return

    network.update_timer += time.dt

    if network.update_timer >= network.update_rate:
        network.update_timer -= network.update_rate
        new_state = PhysicalState(my_char)
        for conn in network.peer.get_connections():
            network.peer.request_update_pstate(conn, network.my_uuid, new_state)
