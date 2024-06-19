# Handles all world generation.
from ursina import *
import json
import os

from .character import Character

tuple_vars = ["origin", "position", "world_position", "rotation", "world_rotation", "texture_scale"]

class GenerateWorld:
    def __init__(self, file):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        path = os.path.abspath(os.path.dirname(__file__))
        self.zones_path = os.path.join(path, "..", "data", "zones")
        zonepath = os.path.join(self.zones_path, file)
        if "json" in zonepath:
            self.parse_json(zonepath)

    def parse_json(self, file):
        with open(file) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky":
                Sky(**data)
            else:
                Entity(**self.parse_colors_tuples(data))

    def create_npcs(self, file):
        """Spawn npcs.

        file: str, name of file to load in data/zones. Not full path"""
        path = os.path.join(self.zones_path, file)
        with open(path) as f:
            npc_data = json.load(f)
        return [Character(**self.parse_colors_tuples(data)) for (npc, data) in npc_data.items()]

    def parse_colors_tuples(self, data):
        if "color" in data:
            data["color"] = color.colors[data["color"]]
        for var in tuple_vars:
            if var in data:
                data[var] = [float(a) for a in data[var].split(", ")]
        return data