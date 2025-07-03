"""Handles all procedures relevant to connecting to the server. This should probably be re-segmented
since the networking refactoring"""
from ursina import destroy
from ursina.networking import rpc

from .network import network
from .register import *
from .world_requests import request_enter_world
from ..gamestate import gs
from ..states import get_player_states_from_json

def input(key):
    """Right now, handles login inputs. Very temporary framework.
    If hosting, do all the things needed to create the world.
    If not hosting, just connect and let on_connect handle the rest.
    """
    if not network.peer.is_running():
        if key == "c":
            print("Attempting to connect")
            network.peer.start("localhost", 8080, is_host=False)

@rpc(network.peer)
def on_connect(connection, time_connected):
    """What a client should do when they connect.
    Host just needs to make a new character, map connection/uuid to it, increment uuid,
    and send the new character to peers.
    Will need to generate world on peer, spawn all characters including
    peer's, and bind peer's character to my_uuid.
    Eventually, this will not be done on connection, it will be done on "enter world"."""
    if not network.peer.is_hosting():
        gs.pname = "Demo Player"
        pstate, cbstate, equipment, inventory, skills, powers = \
            get_player_states_from_json(gs.pname)
        network.peer.request_enter_world(connection, pstate, cbstate, equipment, inventory, skills, powers)