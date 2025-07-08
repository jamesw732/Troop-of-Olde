"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import ClientCharacter
from .controllers import PlayerController, NPCController
from .. import data_path, get_npc_states_from_data, network

class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.structures = []
        self.pc = None
        self.pc_ctrl = None

    def load_zone(self, file):
        """Load the world by parsing a json

        file: str, name of file to load in data/zones. Not full path."""
        zonepath = os.path.join(self.zones_path, file)
        with open(zonepath) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky":
                self.structures.append(Sky(**data))
            else:
                if "color" in data and isinstance(data["color"], str):
                    data["color"] = color.colors[data["color"]]
                self.structures.append(Entity(**data))

    def make_pc(self, uuid, pstate, equipment, inventory, skills, powers, cbstate):
        """Makes the player character while updating uuid map"""
        def on_destroy():
            del network.uuid_to_char[uuid]
        self.pc = ClientCharacter(uuid, pstate=pstate, equipment=equipment, inventory=inventory,
                                  skills=skills, powers=powers, cbstate=cbstate, on_destroy=on_destroy)
        network.uuid_to_char[uuid] = self.pc

    def make_pc_ctrl(self):
        """Makes the player character controller while updating uuid map.
        Relies on make_pc being called"""
        if world.pc is None:
            return
        uuid = world.pc.uuid
        def on_destroy():
            del network.uuid_to_ctrl[uuid]
        char = network.uuid_to_char[uuid]
        self.pc_ctrl = PlayerController(character=char, on_destroy=on_destroy)
        network.uuid_to_ctrl[uuid] = self.pc_ctrl
        
    def make_npc(self, uuid, pstate, cbstate):
        """Makes an npc while updating uuid map"""
        def on_destroy():
            del network.uuid_to_char[uuid]
        self.pc = ClientCharacter(uuid, pstate=pstate, cbstate=cbstate, on_destroy=on_destroy)
        network.uuid_to_char[uuid] = self.pc

    def make_npc_ctrl(self, uuid):
        """Makes an npc controller while updating uuid map.
        Relies on make_npc being called"""
        def on_destroy():
            del network.uuid_to_ctrl[uuid]
        char = network.uuid_to_char[uuid]
        self.pc_ctrl = NPCController(character=char, on_destroy=on_destroy)

world = World()