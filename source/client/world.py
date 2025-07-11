"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import ClientCharacter
from .controllers import PlayerController, NPCController
from .. import *

class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.structures = []
        self.pc = None
        self.pc_ctrl = None

        self.uuid_to_char = dict()
        self.uuid_to_ctrl = dict()
        self.inst_id_to_item = dict()
        self.inst_id_to_power = dict()
        self.inst_id_to_container = dict()

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

    def make_pc(self, uuid, **kwargs):
        """Create the Player Character from the server's inputs.

        kwargs obtained from network.peer.spawn_pc:
        uuid: unique id. Used to refer to Characters over network.
        pstate: PhysicalState; defines physical attrs
        cbstate: PlayerCombatState which overwrites 
        equipment: list whose first element is a container id, then rest of elements
        are tuples of (item id, inst item id)
        inventory: list whose first element is a container id, then rest of elements
        are tuples of (item id, inst item id)
        skills: SkillsState
        powers: list whose elements are tuples of (power id, inst power id)
        """
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
        self.pc = ClientCharacter(uuid, **kwargs, on_destroy=on_destroy)
        self.uuid_to_char[uuid] = self.pc
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
        
    def make_npc(self, uuid, pstate, cbstate):
        """Makes an npc while updating uuid map"""
        def on_destroy():
            char = self.uuid_to_char[uuid]
            del self.uuid_to_char[uuid]
            char.model_child.detachNode()
            del char.model_child
            for src in char.targeted_by:
                src.target = None
            self.pc.ignore_traverse.remove(char.clickbox)
            del char
        new_char = ClientCharacter(uuid, pstate=pstate, cbstate=cbstate, on_destroy=on_destroy)
        self.uuid_to_char[uuid] = new_char
        if self.pc:
            self.pc.ignore_traverse.append(new_char.clickbox)

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

    def make_container_from_ids(self, name, ids, default_size):
        container_id = ids[0]
        item_ids = ids[1:]
        items = [None] * default_size
        for i, (item_id, inst_id) in enumerate(item_ids):
            if item_id < 0:
                continue
            items[i] = self.make_item(item_id, inst_id)
        container = Container(container_id, name, items)
        self.inst_id_to_container[container_id] = container
        return container

    def make_item(self, item_id, inst_id):
        def on_destroy():
            del self.inst_id_to_item[inst_id]
        item = Item(item_id, inst_id, on_destroy=on_destroy)
        self.inst_id_to_item[inst_id] = item
        return item

    def make_powers_from_ids(self, power_ids):
        powers = [None] * default_num_powers
        for i, (power_id, inst_id) in enumerate(power_ids):
            if power_id < 0 or inst_id < 0:
                continue
            powers[i] = self.make_power(power_id, inst_id)
        return powers

    def make_power(self, power_id, inst_id):
        power = Power(power_id, inst_id)
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