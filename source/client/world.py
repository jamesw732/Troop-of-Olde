"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .. import data_path, get_npc_states_from_data


class World:
    def __init__(self):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        self.entities = []
        self.chars = []
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
                self.entities.append(Sky(**data))
            else:
                if "color" in data and isinstance(data["color"], str):
                    data["color"] = color.colors[data["color"]]
                self.entities.append(Entity(**data))


world = World()