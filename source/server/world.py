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
        for (entity, data) in world_data.items():
            if entity == "Sky":
                continue
            if "color" in data:
                data["color"] = color.colors[data["color"]]
            Entity(**data)

    def load_npcs(self, file):
        """Spawn from the npc source file. Called only by server.

        file: str, name of file to load in data/zones. Not full path"""
        path = os.path.join(self.zones_path, file)
        with open(path) as f:
            npc_data = json.load(f)
        npcs = [self.make_char(**get_npc_states_from_data(data, name))
                                for name, data in npc_data.items()]
        for npc in npcs:
            self.make_ctrl(npc.uuid)

    def make_char(self, **kwargs):
        """Makes the player character while updating uuid map"""
        uuid = self.uuid_counter
        self.uuid_counter += 1
        if "equipment" in kwargs:
            kwargs["equipment"] = self.make_container_from_ids("equipment",
                                                               kwargs["equipment"],
                                                               num_equipment_slots)
        if "inventory" in kwargs:
            kwargs["inventory"] = self.make_container_from_ids("inventory",
                                                               kwargs["inventory"],
                                                               num_inventory_slots)
        if "powers" in kwargs:
            kwargs["powers"] = self.make_powers_from_ids(kwargs["powers"])
        def on_destroy():
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
        new_char = ServerCharacter(uuid, **kwargs, on_destroy=on_destroy)
        self.uuid_to_char[uuid] = new_char
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

    def make_container_from_ids(self, name, item_ids, default_size):
        """Creates a container from client inputs.

        name: str name of this container
        item_ids: list of int item database ids"""
        container_id = self.container_inst_id_ct
        self.container_inst_id_ct += 1
        items = [None] * default_size
        for i, item_id in enumerate(item_ids):
            if item_id < 0:
                continue
            items[i] = self.make_item(item_id)
        container = Container(container_id, name, items)
        self.inst_id_to_container[container_id] = container
        return container

    def make_item(self, item_id):
        inst_id = self.item_inst_id_ct
        self.item_inst_id_ct += 1
        def on_destroy():
            del self.inst_id_to_item[inst_id]
        item = Item(item_id, inst_id, on_destroy=on_destroy)
        self.inst_id_to_item[inst_id] = item
        return item
    
    def make_powers_from_ids(self, power_ids):
        powers = [None] * default_num_powers
        for i, power_id in enumerate(power_ids):
            if power_id < 0:
                continue
            powers[i] = self.make_power(power_id)
        return powers

    def make_power(self, power_id):
        inst_id = self.power_inst_id_ct
        self.power_inst_id_ct += 1
        power = ServerPower(power_id, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power

    def container_to_ids(self, container, id_type="inst_id"):
        """Convert a container (Character attribute) to one sendable over the network

        container: list containing Items
        id_type: the literal id attribute of the item, or tuple of id attributes
        In the latter case, returns a 1d list stacked in order of the id attributes"""
        if isinstance(id_type, tuple):
            return [getattr(item, id_subtype) if hasattr(item, id_subtype) else -1 
                        for id_subtype in id_type
                    for item in container]
        return [getattr(item, id_type) if hasattr(item, id_type) else -1 for item in container]

    def ids_to_container(self, id_container):
        """Convert container of inst ids to a list of objects"""
        return [self.inst_id_to_item.get(itemid, None) for itemid in id_container]

world = World()