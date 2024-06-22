from ursina import *
from ursina.networking import *

import os

from .base import *
from ..character import Character
from ..npc_controller import NPC_Controller
from ..gamestate import *
from ..player_controller import PlayerController
from ..world_gen import GenerateWorld


def serialize_combat_state(writer, state):
    for attr in combat_state_attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                writer.write(attr)
                writer.write(val)
    writer.write("end")

def deserialize_combat_state(reader):
    state = CombatState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        if attr == "end":
            return state
        val = reader.read(combat_state_attrs[attr])
        setattr(state, attr, val)


def serialize_physical_state(writer, state):
    for attr in phys_state_attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                if attr == "target":
                    # Don't write the character, write its uuid
                    val = val.uuid
                writer.write(attr)
                writer.write(val)
    writer.write("end")

def deserialize_physical_state(reader):
    state = PhysicalState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        if attr == "end":
            return state
        val = reader.read(phys_state_attrs[attr])
        setattr(state, attr, val)


network.peer.register_type(PhysicalState, serialize_physical_state,
                           deserialize_physical_state)
network.peer.register_type(CombatState, serialize_combat_state,
                           deserialize_combat_state)

# This is a very primitive approach to logins. This will eventually become part of GUI code.
def input(key):
    if not network.peer.is_running():
        if key == "h":
            pstate = PhysicalState(speed=20.0, model='cube', color="orange",
                                   scale=(1, 2, 1), collider="box",
                                   origin=(0, -0.5, 0), position=(0, 1, 0))
            cbstate = CombatState(maxhealth=100, health=100)
            char = Character(name="Player", pstate=pstate, cbstate=cbstate)
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
        new_pstate = PhysicalState(speed=20.0, model='cube', color="orange",
                               scale=(1, 2, 1), collider="box", origin=(0, -0.5, 0),
                               position=(0, 1, 0))
        new_cbstate = CombatState(maxhealth=100, health=100)
        char = Character(name="Player", pstate=new_pstate, cbstate=new_cbstate)
        char.uuid = network.uuid_counter
        network.uuid_to_char[char.uuid] = char
        network.uuid_counter += 1
        gs.chars.append(char)
        network.connection_to_char[connection] = char
        network.peer.generate_world(connection, "demo.json")
        for conn in network.peer.get_connections():
            # New user needs all characters
            if conn == connection:
                for ch in gs.chars:
                    pstate = ch.get_physical_state()
                    cstate = ch.get_combat_state()
                    network.peer.spawn_character(conn, ch.uuid, pstate, cstate)
            # Existing users just need new character
            else:
                network.peer.spawn_character(conn, char.uuid, new_pstate, new_cbstate)
        network.peer.bind_uuid_to_char(connection, char.uuid)

@rpc(network.peer)
def generate_world(connection, time_received, zone:str):
    gs.world = GenerateWorld(zone)

@rpc(network.peer)
def spawn_character(connection, time_received, uuid: int,
                    phys_state: PhysicalState, cb_state: CombatState):
    if network.peer.is_hosting():
        return
    if uuid not in network.uuid_to_char:
        char = Character(pstate=phys_state, cbstate=cb_state)
        gs.chars.append(char)
        network.uuid_to_char[uuid] = char
        char.uuid = uuid

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