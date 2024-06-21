from ursina import *
from ursina.networking import *

import os

from .base import *
from ..character import Character
from ..npc_controller import NPC_Controller
from ..gamestate import *
from ..physics import PhysicalState, serialize_physical_state, deserialize_physical_state
from ..player_controller import PlayerController
from ..world_gen import GenerateWorld


network.peer.register_type(PhysicalState, serialize_physical_state,
                           deserialize_physical_state)

# This is a very primitive approach to logins. This will eventually become part of GUI code.
def input(key):
    if not network.peer.is_running():
        if key == "h":
            char = Character("Player", speed=20.0, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
            network.my_uuid = network.uuid_counter
            network.uuid_counter += 1
            char.uuid = network.my_uuid
            network.uuid_to_char[network.my_uuid] = char
            gs.chars.append(char)
            char.ignore_traverse = gs.chars
            gs.pc = PlayerController(char, peer=network.peer)

            gs.world = GenerateWorld("demo.json")
            npcs = gs.world.create_npcs("demo_npcs.json")
            gs.chars += npcs
            for npc in npcs:
                npc.controller = NPC_Controller(npc, char)
                npc.uuid = network.uuid_counter
                network.uuid_to_char[npc.uuid] = npc
                network.uuid_counter += 1

            network.peer.start("localhost", 8080, is_host=True)
        elif key == "c":
            print("Attempting to connect")
            network.peer.start("localhost", 8080, is_host=False)

@rpc(network.peer)
def on_connect(connection, time_connected):
    """What host should do when there's a new connection
    Host just needs to make a new character, map connection/uuid to it, increment uuid,
    and send the new character to peers.
    Will need to generate world on peer, spawn all characters including
    peer's, and bind peer's character to my_uuid.
    Eventually, this will not be done on connection, it will be done on "enter world"."""
    if network.peer.is_hosting():
        char = Character(name="Player", speed=20.0, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
        char.uuid = network.uuid_counter
        network.uuid_to_char[char.uuid] = char
        network.uuid_counter += 1
        gs.chars.append(char)
        network.connection_to_char[connection] = char
        new_state = char.get_physical_state()
        network.peer.generate_world(connection, "demo.json")
        states = [c.get_physical_state() for c in gs.chars]
        for conn in network.peer.get_connections():
            if conn == connection:
                for state in states:
                    network.peer.spawn_character(conn, state)
            else:
                network.peer.spawn_character(conn, new_state)
        network.peer.bind_uuid_to_char(connection, char.uuid)

@rpc(network.peer)
def generate_world(connection, time_received, zone:str):
    global world
    world = GenerateWorld(zone)

@rpc(network.peer)
def spawn_character(connection, time_received, char_state:PhysicalState):
    if network.peer.is_hosting():
        return
    if char_state.uuid not in network.uuid_to_char:
        char = Character(state=char_state)
        gs.chars.append(char)
        network.uuid_to_char[char_state.uuid] = char

@rpc(network.peer)
def bind_uuid_to_char(connection, time_received, uuid:int):
    if network.peer.is_hosting():
        return
    network.my_uuid = uuid
    char = network.uuid_to_char.get(uuid)
    if char:
        char.ignore_traverse = gs.chars
        gs.pc = PlayerController(char, network.peer)
        gs.pc.character = char
        char.controller = gs.pc