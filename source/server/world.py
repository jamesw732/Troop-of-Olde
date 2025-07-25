"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import ServerCharacter
from .controllers import MobController
from .power import ServerPower
from .. import *


class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.entities = []

        self.uuid_to_char = dict()
        self.uuid_to_ctrl = dict()
        self.uuid_counter = 0

        self.inst_id_to_item = dict()
        self.item_inst_id_ct = 0
        self.inst_id_to_power = dict()
        self.power_inst_id_ct = 0
        self.inst_id_to_container = dict()
        self.container_inst_id_ct = 0

    def load_zone(self, file):
        """Load the world by parsing a json

        file: str, name of file to load in data/zones. Not full path."""
        zonepath = os.path.join(self.zones_path, file)
        with open(zonepath) as f:
            world_data = json.load(f)
        for name, data in world_data["entities"].items():
            if "color" in data and isinstance(data["color"], str):
                data["color"] = color.colors[data["color"]]
            Entity(**data)
        for name, data in world_data["npcs"].items():
            data["cname"] = name
            init_dict = self.make_npc_init_dict(data)
            npc = self.make_char(init_dict)
            self.make_ctrl(npc.uuid)

    def make_npc_init_dict(self, npc_data):
        login_state = LoginState(npc_data)
        return self.make_char_init_dict(login_state)

    def make_char_init_dict(self, login_state):
        """Converts data from a LoginState to a dict that can be input into ServerCharacter"""
        init_dict = dict()
        uuid = self.uuid_counter
        init_dict["uuid"] = uuid
        self.uuid_counter += 1
        # Need to loop over States to access by key
        for key in default_char_attrs:
            if key in login_state.statedef:
                init_dict[key] = login_state[key]
        # Make equipment
        equipment_id = self.container_inst_id_ct
        self.container_inst_id_ct += 1
        items = [self.make_item(item_id) if item_id >= 0 else None
                 for item_id in login_state["equipment"]]
        items += [None] * (len(items) - num_equipment_slots)
        equipment = Container(equipment_id, "equipment", items)
        self.inst_id_to_container[equipment_id] = equipment
        init_dict["equipment"] = equipment
        # Make inventory
        inventory_id = self.container_inst_id_ct
        self.container_inst_id_ct += 1
        items = [self.make_item(item_id) if item_id >= 0 else None
                 for item_id in login_state["inventory"]]
        items += [None] * (len(items) - num_inventory_slots)
        inventory = Container(inventory_id, "inventory", items)
        self.inst_id_to_container[inventory_id] = inventory
        init_dict["inventory"] = inventory
        # Make powers
        powers = [self.make_power(power_mnem) if power_mnem != "" else None
                  for power_mnem in login_state["powers"]]
        powers += [None] * (len(powers) - default_num_powers)
        init_dict["powers"] = powers
        on_destroy = self.make_char_on_destroy(uuid)
        init_dict["on_destroy"] = on_destroy
        return init_dict

    def make_char_on_destroy(self, uuid):
        def on_destroy():
            if uuid not in self.uuid_to_char:
                return
            char = self.uuid_to_char[uuid]
            del self.uuid_to_char[uuid]
            for src in char.targeted_by:
                src.target = None
            char.targeted_by = []
            # Loop over copy of effects
            for effect in list(char.effects):
                effect.remove()
            del char
            if uuid in network.uuid_to_connection:
                connection = network.uuid_to_connection[uuid]
                del network.uuid_to_connection[uuid]
                del network.connection_to_uuid[connection]
        return on_destroy

    def make_char(self, init_dict):
        """Makes a character from init_dict while updating uuid map

        init_dict is obtained from World.make_char_init_dict"""
        new_char = ServerCharacter(**init_dict)
        self.uuid_to_char[new_char.uuid] = new_char
        return new_char

    def make_ctrl(self, uuid):
        """Makes the player character controller while updating uuid map.
        Relies on make_pc being called"""
        def on_destroy():
            ctrl = self.uuid_to_ctrl[uuid]
            del self.uuid_to_ctrl[uuid]
            del ctrl.character
            del ctrl
        char = self.uuid_to_char[uuid]
        new_ctrl = MobController(character=char, on_destroy=on_destroy)
        self.uuid_to_ctrl[uuid] = new_ctrl
        return new_ctrl

    def make_item(self, item_id):
        inst_id = self.item_inst_id_ct
        self.item_inst_id_ct += 1
        def on_destroy():
            del self.inst_id_to_item[inst_id]
        item = Item(item_id, inst_id, on_destroy=on_destroy)
        self.inst_id_to_item[inst_id] = item
        return item
    
    def make_power(self, power_mnem):
        inst_id = self.power_inst_id_ct
        self.power_inst_id_ct += 1
        power = ServerPower(power_mnem, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power

    def container_to_ids(self, container, id_type="inst_id"):
        """Convert a container of items/powers to a container of ids, sendable over network.

        container: list containing Items
        id_type: the literal id attribute of the item"""
        return [getattr(item, id_type) if hasattr(item, id_type) else -1 for item in container]

    def ids_to_container(self, id_container):
        """Convert container of inst ids to a list of objects"""
        return [self.inst_id_to_item.get(itemid, None) for itemid in id_container]

world = World()