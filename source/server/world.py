"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import ServerCharacter
from .controllers import MobController
from .. import *


class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.entities = []
        self.pc = None

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
        uuid = network.uuid_counter
        network.uuid_counter += 1
        if "equipment" in kwargs:
            kwargs["equipment"] = self.make_container_from_ids("equipment",
                                                               kwargs["equipment"],
                                                               num_equipment_slots)
        if "inventory" in kwargs:
            kwargs["inventory"] = self.make_container_from_ids("inventory",
                                                               kwargs["inventory"],
                                                               num_inventory_slots)
        def on_destroy():
            del network.uuid_to_char[uuid]
            if uuid in network.uuid_to_connection:
                connection = network.uuid_to_connection[uuid]
                del network.uuid_to_connection[uuid]
                del network.connection_to_char[connection]
        new_char = ServerCharacter(uuid, **kwargs, on_destroy=on_destroy)
        network.uuid_to_char[uuid] = new_char
        return new_char

    def make_ctrl(self, uuid):
        """Makes the player character controller while updating uuid map.
        Relies on make_pc being called"""
        def on_destroy():
            del network.uuid_to_ctrl[uuid]
        char = network.uuid_to_char[uuid]
        new_ctrl = MobController(character=char, on_destroy=on_destroy)
        network.uuid_to_ctrl[uuid] = new_ctrl
        return new_ctrl

    def make_container_from_ids(self, name, item_ids, default_size):
        """Creates a container from client inputs.

        name: str name of this container
        item_ids: list of int item database ids"""
        container_id = network.container_inst_id_ct
        network.container_inst_id_ct += 1
        items = [None] * default_size
        for i, item_id in enumerate(item_ids):
            if item_id < 0:
                continue
            items[i] = self.make_item(item_id)
        container = Container(container_id, name, items)
        network.inst_id_to_container[container_id] = container
        return container

    def make_item(self, item_id):
        inst_id = network.item_inst_id_ct
        network.item_inst_id_ct += 1
        def on_destroy():
            del network.inst_id_to_item[inst_id]
        item = Item(item_id, inst_id, on_destroy=on_destroy)
        network.inst_id_to_item[inst_id] = item
        return item

world = World()