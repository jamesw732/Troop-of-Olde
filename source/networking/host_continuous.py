"""Host is responsible for continuously updating information like health for all characters"""
from ursina import time
from ursina.networking import rpc

from .network import network
from .world_responses import *
from ..gamestate import gs
from ..states.state import State


def update():
    network.peer.update()
    # No point updating if no peers
    if not (network.peer.is_running() and network.peer.connection_count() > 0):
        return

    network.update_timer += time.dt
    if network.update_timer >= network.update_rate:
        network.update_timer -= network.update_rate
        connections = network.peer.get_connections()
        for char in gs.chars:
            mini_state = State("npc_combat", char)
            for connection in connections:
                if connection not in network.connection_to_char:
                    continue
                if network.connection_to_char[connection] is char:
                    network.peer.update_pc_cbstate(connection, char.uuid,
                                                   State("pc_combat", char))
                else:
                    network.peer.update_npc_cbstate(connection, char.uuid,
                                                    mini_state)

