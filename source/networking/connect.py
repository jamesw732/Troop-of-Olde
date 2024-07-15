from ursina import destroy
from ursina.networking import rpc

from .base import network
from ..character import Character, get_character_states_from_json
from ..npc_controller import NPC_Controller
from ..gamestate import gs
from ..player_controller import PlayerController
from ..world_gen import GenerateWorld
from ..ui.main import make_all_ui
from ..states.cbstate_complete import CompleteCombatState, serialize_complete_cb_state, \
        deserialize_complete_cb_state
from ..states.cbstate_base import BaseCombatState, serialize_base_cb_state, deserialize_base_cb_state
from ..states.cbstate_mini import MiniCombatState, serialize_mini_state, deserialize_mini_state
from ..states.container import InitContainer, serialize_init_container, deserialize_init_container
from ..states.physicalstate import PhysicalState, serialize_physical_state, deserialize_physical_state
from ..states.stat_change import StatChange, serialize_stat_change, deserialize_stat_change

# Actually register the states as types sendable over the network
network.peer.register_type(PhysicalState, serialize_physical_state,
                           deserialize_physical_state)
network.peer.register_type(CompleteCombatState, serialize_complete_cb_state,
                           deserialize_complete_cb_state)
network.peer.register_type(BaseCombatState, serialize_base_cb_state,
                           deserialize_base_cb_state)
network.peer.register_type(InitContainer, serialize_init_container, deserialize_init_container)
network.peer.register_type(MiniCombatState, serialize_mini_state,
                           deserialize_mini_state)
network.peer.register_type(StatChange, serialize_stat_change, deserialize_stat_change)


def input(key):
    """Right now, handles login inputs. Very temporary framework.
    If hosting, do all the things needed to create the world.
    If not hosting, just connect and let on_connect handle the rest.
    """
    if not network.peer.is_running():
        if key == "h":
            pname = "Demo Player"
            pstate, basestate, equipment, inventory = \
                get_character_states_from_json(pname)
            char = Character(pstate=pstate, base_state=basestate, equipment=equipment,
                             inventory=inventory)
            network.my_uuid = network.uuid_counter
            network.uuid_counter += 1
            char.uuid = network.my_uuid
            network.uuid_to_char[network.my_uuid] = char
            gs.chars.append(char)
            char.ignore_traverse = gs.chars
            gs.pc = char
            gs.playercontroller = PlayerController(char, peer=network.peer)

            gs.world = GenerateWorld("demo.json")
            npcs = gs.world.create_npcs("demo_npcs.json")
            gs.chars += npcs
            for npc in npcs:
                npc.controller = NPC_Controller(npc, char)
                npc.uuid = network.uuid_counter
                network.uuid_to_char[npc.uuid] = npc
                network.uuid_counter += 1

            network.peer.start("localhost", 8080, is_host=True)
            make_all_ui()
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
    if not network.peer.is_hosting():
        gs.pname = "Demo Player"
        pstate, base_state, equipment, inventory = \
            get_character_states_from_json(gs.pname)
        gs.pc = Character(pstate=pstate, base_state=base_state, equipment=equipment, inventory=inventory)
        network.peer.request_enter_world(connection, pstate, base_state, equipment, inventory)

@rpc(network.peer)
def request_enter_world(connection, time_received, new_pstate: PhysicalState,
                        base_state: BaseCombatState, equipment: InitContainer,
                        inventory: InitContainer):
    if network.peer.is_hosting():
        char = Character(pstate=new_pstate, base_state=base_state,
                         equipment=equipment, inventory=inventory)
        print(char.inventory)
        char.uuid = network.uuid_counter
        network.uuid_to_char[char.uuid] = char
        network.uuid_counter += 1
        gs.chars.append(char)
        network.connection_to_char[connection] = char
        network.peer.generate_world(connection, "demo.json")
        new_mini_state = MiniCombatState(char)
        for conn in network.peer.get_connections():
            # New user needs all characters except own
            if conn == connection:
                for ch in gs.chars:
                    pstate = PhysicalState(ch)
                    if ch is char:
                        continue
                    # The player won't be able to see everything about other characters
                    else:
                        cstate = MiniCombatState(ch)
                        network.peer.spawn_npc(conn, ch.uuid, pstate, cstate)
            # Existing users just need new character
            else:
                network.peer.spawn_npc(conn, char.uuid, new_pstate, new_mini_state)
        network.peer.bind_pc(connection, char.uuid)
        network.peer.make_ui(connection)
        # Send over instantiated item id's
        inst_inventory = InitContainer({str(i): item.uiid for i, item
                          in enumerate(char.inventory) if item is not None})
        inst_equipment = InitContainer({k: item.uiid for k, item
                          in char.equipment.items() if item is not None})
        network.peer.bind_pc_items(connection, inst_inventory, inst_equipment)

@rpc(network.peer)
def generate_world(connection, time_received, zone:str):
    """Remotely generate the world"""
    gs.world = GenerateWorld(zone)

@rpc(network.peer)
def bind_pc(connection, time_received, uuid: int):
    """Remotely bind player character to uuid and player controller"""
    if network.peer.is_hosting():
        return
    if uuid not in network.uuid_to_char:
        gs.playercontroller = PlayerController(gs.pc, network.peer)
        gs.pc.controller = gs.playercontroller

        gs.chars.append(gs.pc)
        gs.pc.ignore_traverse = gs.chars

        network.uuid_to_char[uuid] = gs.pc
        gs.pc.uuid = uuid
        network.my_uuid = uuid

@rpc(network.peer)
def bind_pc_items(connection, time_received, inventory: InitContainer, equipment: InitContainer):
    for i, uiid in inventory.items():
        gs.pc.inventory[int(i)].uiid = uiid
        network.uiid_to_item[uiid] = gs.pc.inventory[int(i)]
    for k, uiid in equipment.items():
        gs.pc.equipment[k].uiid = uiid
        network.uiid_to_item[uiid] = gs.pc.equipment[k]

@rpc(network.peer)
def spawn_npc(connection, time_received, uuid: int,
              phys_state: PhysicalState, mini_state: MiniCombatState):
    """Remotely spawn a character that isn't the client's player character (could also be other players)"""
    if network.peer.is_hosting():
        return
    if uuid not in network.uuid_to_char:
        char = Character(pstate=phys_state, mini_state=mini_state)
        gs.chars.append(char)
        network.uuid_to_char[uuid] = char
        char.uuid = uuid

@rpc(network.peer)
def make_ui(connection, time_received):
    """Remotely tell a client to make the game UI"""
    make_all_ui()
