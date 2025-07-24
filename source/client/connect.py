"""Handles all procedures relevant to connecting to the server. This should probably be re-segmented
since the networking refactoring"""
import os
import json

from ursina.networking import rpc

from .world import world
from .. import network


@rpc(network.peer)
def on_connect(connection, time_received):
    """What a client should do when they connect.
    Host just needs to make a new character, map connection/uuid to it, increment uuid,
    and send the new character to peers.
    Will need to generate world on peer, spawn all characters including
    peer's, and bind peer's character to my_uuid.
    Eventually, this will not be done on connection, it will be done upon entering the world."""
    network.server_connection = connection
    player_name = "Demo Player"
    login_state = world.load_player_data(player_name)
    network.peer.request_enter_world(connection, login_state)

@rpc(network.peer)
def on_disconnect(connection, time_received):
    """What a client should do when disconnecting.
    Right now, this is blank because there's nothing to do upon disconnection.
    Once I implement a real client, this will be populated"""
    pass
