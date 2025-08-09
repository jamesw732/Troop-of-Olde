"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os
import glob

from .character import ClientCharacter
from .controllers import PlayerController, NPCController
from .power_system import PowerSystem
from .ui import ui
from .. import *

class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.pc = None
        self.pc_ctrl = None
        self.init_data = {}

        self.uuid_to_char = dict()
        self.uuid_to_ctrl = dict()
        self.inst_id_to_item = dict()
        self.inst_id_to_power = dict()
        self.inst_id_to_container = dict()

        self.power_system = None

        glb_models = glob.glob("*.glb", root_dir=models_path)
        for path in glb_models:
            load_model(path, folder=models_path)

    def load_zone(self, file):
        """Load the world by parsing a json

        file: str, name of file to load in data/zones. Not full path."""
        zonepath = os.path.join(self.zones_path, file)
        with open(zonepath) as f:
            world_data = json.load(f)
        Sky(**world_data["sky"])
        for name, data in world_data["entities"].items():
            if "color" in data and isinstance(data["color"], str):
                data["color"] = color.colors[data["color"]]
            Entity(**data)

    def load_player_data(self, cname):
        """Loads player data from players.json as a LoginState"""
        players_path = os.path.join(data_path, "players.json")
        with open(players_path) as players:
            pc_data = json.load(players)[cname]
        pc_data["cname"] = cname
        # Pad containers with fill
        pc_data["equipment"] = pc_data["equipment"] \
            + [""] * (num_equipment_slots - len(pc_data["equipment"]))
        pc_data["inventory"] = pc_data["inventory"] \
            + [""] * (num_inventory_slots - len(pc_data["inventory"]))
        pc_data["powers"] = pc_data["powers"] \
            + [""] * (default_num_powers - len(pc_data["powers"]))
        self.init_data["equipment"] = pc_data["equipment"]
        self.init_data["inventory"] = pc_data["inventory"]
        self.init_data["powers"] = pc_data["powers"]
        login_state = LoginState(pc_data)
        return login_state

    def make_pc_init_dict(self, spawn_state):
        """Converts data from a PCSpawnState to a dict that can be input into ServerCharacter"""
        init_dict = dict()
        # Need to loop over States to access by key
        for key in default_char_attrs:
            if key in spawn_state.statedef:
                init_dict[key] = spawn_state[key]
        # Make equipment
        equipment_id = spawn_state["equipment_id"]
        equipment_inst_ids = spawn_state["equipment_inst_ids"]
        items = [self.make_item(item_mnem, inst_id) if item_mnem != "" and inst_id >= 0
                    else None
                 for item_mnem, inst_id in zip(self.init_data["equipment"], equipment_inst_ids)]
        equipment = Container(equipment_id, "equipment", items)
        self.inst_id_to_container[equipment_id] = equipment
        init_dict["equipment"] = equipment
        # Make inventory
        inventory_id = spawn_state["inventory_id"]
        inventory_inst_ids = spawn_state["inventory_inst_ids"]
        items = [self.make_item(item_mnem, inst_id) if item_mnem != "" and inst_id >= 0
                    else None
                 for item_mnem, inst_id in zip(self.init_data["inventory"], inventory_inst_ids)]
        inventory = Container(inventory_id, "inventory", items)
        self.inst_id_to_container[inventory_id] = inventory
        init_dict["inventory"] = inventory
        # Make powers
        powers_inst_ids = spawn_state["powers_inst_ids"]
        powers = [self.make_power(power_mnem, inst_id) if power_mnem != "" and inst_id >= 0
                    else None
                 for power_mnem, inst_id in zip(self.init_data["powers"], powers_inst_ids)]
        init_dict["powers"] = powers
        on_destroy = self.make_pc_on_destroy(init_dict["uuid"])
        init_dict["on_destroy"] = on_destroy
        return init_dict

    def make_npc_init_dict(self, spawn_state):
        """Converts data from a PCSpawnState to a dict that can be input into ServerCharacter"""
        init_dict = dict(spawn_state)
        on_destroy = self.make_npc_on_destroy(init_dict["uuid"])
        init_dict["on_destroy"] = on_destroy
        return init_dict

    def make_pc_on_destroy(self, uuid):
        def on_destroy():
            self.pc = None
            char = self.uuid_to_char[uuid]
            del self.uuid_to_char[uuid]
            char.model_child.detachNode()
            del char.model_child
            for src in char.targeted_by:
                src.target = None
            char.targeted_by = []
            char.ignore_traverse = []
            del char
        return on_destroy

    def make_npc_on_destroy(self, uuid):
        def on_destroy():
            char = self.uuid_to_char[uuid]
            del self.uuid_to_char[uuid]
            char.model_child.detachNode()
            del char.model_child
            for src in char.targeted_by:
                src.target = None
            self.pc.ignore_traverse.remove(char.clickbox)
            del char
        return on_destroy

    def make_pc(self, init_dict):
        """Create the Player Character from the server's inputs.

        init_dict is a dict obtained from World.make_pc_init_dict
        """
        self.pc = ClientCharacter(**init_dict)
        self.uuid_to_char[self.pc.uuid] = self.pc
        self.pc.ignore_traverse = [char.clickbox for char in self.uuid_to_char.values()]

    def make_pc_ctrl(self):
        """Makes the player character controller while updating uuid map.
        Relies on make_pc being called"""
        if self.pc is None:
            return
        uuid = self.pc.uuid
        def on_destroy():
            del self.uuid_to_ctrl[uuid]
            self.pc_ctrl = None
        char = self.uuid_to_char[uuid]
        self.pc_ctrl = PlayerController(character=char, on_destroy=on_destroy)
        self.uuid_to_ctrl[uuid] = self.pc_ctrl

    def make_power_system(self):
        if self.pc is None:
            return
        self.power_system = PowerSystem(self.pc)
        
    def make_npc(self, init_dict):
        """Create an NPC from the server's inputs.

        init_dict is a dict obtained from World.make_npc_init_dict"""
        new_char = ClientCharacter(**init_dict)
        self.uuid_to_char[new_char.uuid] = new_char
        if self.pc:
            self.pc.ignore_traverse.append(new_char.clickbox)
        return new_char

    def make_npc_ctrl(self, uuid):
        """Makes an npc controller while updating uuid map.
        Relies on make_npc being called"""
        def on_destroy():
            ctrl = self.uuid_to_ctrl[uuid]
            del self.uuid_to_ctrl[uuid]
            del ctrl.character
            destroy(ctrl.namelabel)
            del ctrl.namelabel.char
            del ctrl.namelabel
            del ctrl
        char = self.uuid_to_char[uuid]
        self.uuid_to_ctrl[uuid] = NPCController(character=char, on_destroy=on_destroy)

    def make_item(self, item_mnem, inst_id):
        def on_destroy():
            del self.inst_id_to_item[inst_id]
        item = Item(item_mnem, inst_id, on_destroy=on_destroy)
        self.inst_id_to_item[inst_id] = item
        return item

    def make_power(self, power_mnem, inst_id):
        power = Power(power_mnem, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power


world = World()