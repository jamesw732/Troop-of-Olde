"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import ServerCharacter
from .combat_system import CombatSystem
from .death_system import DeathSystem
from .effect_system import EffectSystem
from .gamestate import GameState
from .items_manager import ItemsManager
from .movement_system import MovementSystem
from .power_system import PowerSystem
from .stat_manager import StatManager
from ..power import Power
from .. import *


class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")

        self.gamestate = GameState()
        self.uuid_counter = 0
        self.uuid_to_char = self.gamestate.uuid_to_char
        self.uuid_to_ctrl = self.gamestate.uuid_to_ctrl
        self.inst_id_to_item = self.gamestate.inst_id_to_item

        self.stat_manager = StatManager(self.gamestate)
        self.combat_system = CombatSystem(self.gamestate, self.stat_manager)
        self.death_system = DeathSystem(self.gamestate)
        self.effect_system = EffectSystem(self.gamestate, self.stat_manager)
        self.items_manager = ItemsManager(self.gamestate, self.stat_manager)
        self.power_system = PowerSystem(self.gamestate, self.effect_system)
        self.movement_system = MovementSystem(self.gamestate)

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
            self.movement_system.add_char(npc)
            # self.make_ctrl(npc.uuid)

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
        items = [self.items_manager.make_item(item_mnem) if item_mnem != ""  else None
                 for item_mnem in login_state["equipment"]]
        items += [None] * (len(items) - num_equipment_slots)
        equipment = Container("equipment", items)
        init_dict["equipment"] = equipment
        # Make inventory
        items = [self.items_manager.make_item(item_mnem) if item_mnem != "" else None
                 for item_mnem in login_state["inventory"]]
        items += [None] * (len(items) - num_inventory_slots)
        inventory = Container("inventory", items)
        init_dict["inventory"] = inventory
        # Make powers
        powers = [self.power_system.make_power(power_mnem) if power_mnem != "" else None
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
            if uuid in self.uuid_to_ctrl:
                ctrl = self.uuid_to_ctrl[uuid]
                destroy(ctrl)
        return on_destroy

    def make_char(self, init_dict):
        """Makes a character from init_dict while updating uuid map

        init_dict is obtained from World.make_char_init_dict"""
        new_char = ServerCharacter(**init_dict)
        self.uuid_to_char[new_char.uuid] = new_char
        # Apply stats from items
        for item in new_char.equipment:
            if item is None:
                continue
            self.stat_manager.apply_state_diff(new_char, item.stats)
        self.stat_manager.update_max_ratings(new_char)
        return new_char


world = World()