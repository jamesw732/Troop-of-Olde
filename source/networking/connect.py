"""Handles all procedures relevant to connecting to the server. This should probably be re-segmented
since the networking refactoring"""
from ursina import destroy
from ursina.networking import rpc

from .network import network
from .register import *
from ..character import Character
from ..npc import NPC
from ..player_character import PlayerCharacter
from ..npc_controller import NPC_Controller
from ..gamestate import gs
from ..player_controller import PlayerController
from ..world_gen import GenerateWorld
from ..ui import *
from ..states import *

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
        pstate, cb_state, equipment, inventory, skills, lexicon = \
            get_character_states_from_json(gs.pname)
        network.peer.request_enter_world(connection, pstate, cb_state, equipment, inventory, skills, lexicon)

@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: State,
                        base_state: State, equipment: IdContainer,
                        inventory: IdContainer, skills: State,
                        lexicon: IdContainer):
    if network.peer.is_hosting():
        new_pc = Character(pstate=pstate, base_state=base_state,
                         equipment=equipment, inventory=inventory, skills=skills,
                         lexicon=lexicon)
        # Could we handle this uuid business in on_connect?
        new_pc.uuid = network.uuid_counter
        network.uuid_counter += 1
        network.uuid_to_char[new_pc.uuid] = new_pc
        network.uuid_to_connection[new_pc.uuid] = connection
        gs.chars.append(new_pc)
        network.connection_to_char[connection] = new_pc
        network.peer.remote_generate_world(connection, "demo.json")
        # The new pc will be an npc for everybody else
        new_npc_cbstate = State("npc_combat", new_pc)
        for conn in network.peer.get_connections():
            if conn == connection:
                for ch in gs.chars:
                    if ch is new_pc:
                        pc_cbstate = State("pc_combat", new_pc)
                        network.peer.spawn_pc(connection, new_pc.uuid, pstate, equipment,
                                              inventory, skills, lexicon, pc_cbstate)
                    else:
                        npc_pstate = State("physical", ch)
                        npc_cbstate = State("npc_combat", ch)
                        network.peer.spawn_npc(conn, ch.uuid, npc_pstate, npc_cbstate)
            # Existing users just need new character
            else:
                network.peer.spawn_npc(conn, new_pc.uuid, pstate, new_npc_cbstate)
        network.peer.make_ui(connection)
        # Send over instantiated item id's
        inst_inventory = IdContainer({k: item.iiid for k, item
                          in new_pc.inventory.items() if item is not None})
        inst_equipment = IdContainer({k: item.iiid for k, item
                          in new_pc.equipment.items() if item is not None})
        network.peer.bind_pc_items(connection, inst_inventory, inst_equipment)
        network.broadcast_cbstate_update(new_pc)

@rpc(network.peer)
def remote_generate_world(connection, time_received, zone:str):
    """Remotely generate the world"""
    gs.world = GenerateWorld(zone)

@rpc(network.peer)
def spawn_pc(connection, time_received, uuid: int, pstate: State, equipment: IdContainer,
             inventory: IdContainer, skills: State, lexicon: IdContainer, cbstate: State):
    gs.pc = PlayerCharacter(pstate=pstate, equipment=equipment, inventory=inventory, skills=skills,
                            lexicon=lexicon, cb_state=cbstate)

    gs.playercontroller = PlayerController(gs.pc)
    gs.pc.controller = gs.playercontroller

    gs.chars.append(gs.pc)
    gs.pc.ignore_traverse = gs.chars

    network.uuid_to_char[uuid] = gs.pc
    gs.pc.uuid = uuid
    network.my_uuid = uuid
    network.server_connection = connection


@rpc(network.peer)
def bind_pc_items(connection, time_received, inventory: IdContainer, equipment: IdContainer):
    for k, iiid in inventory.items():
        gs.pc.inventory[k].iiid = iiid
        network.iiid_to_item[iiid] = gs.pc.inventory[k]
    for k, iiid in equipment.items():
        gs.pc.equipment[k].iiid = iiid
        network.iiid_to_item[iiid] = gs.pc.equipment[k]

@rpc(network.peer)
def spawn_npc(connection, time_received, uuid: int, 
              phys_state: State, cb_state: State):
    """Remotely spawn a character that isn't the client's player character (could also be other players)"""
    if network.peer.is_hosting():
        return
    if uuid not in network.uuid_to_char:
        char = NPC(pstate=phys_state, cb_state=cb_state)
        gs.chars.append(char)
        network.uuid_to_char[uuid] = char
        char.uuid = uuid

@rpc(network.peer)
def make_ui(connection, time_received):
    """Remotely tell a client to make the game UI"""
    gs.ui = UI()
    make_all_ui(gs.ui)
