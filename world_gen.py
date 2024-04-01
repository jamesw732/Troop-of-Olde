# Handles all world generation.
from ursina import *
from npc import *
import json

tuple_vars = ["origin", "position", "world_position", "rotation", "world_rotation", "texture_scale"]

class GenerateWorld:
    def __init__(self, file):
        if "json" in file:
            self.parse_json(file)

    def parse_json(self, file):
        with open(file) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky":
                Sky(**data)
            else:
                Entity(**self.parse_colors_tuples(data))
    
    def create_npcs(self, file):
        with open(file) as f:
            npc_data = json.load(f)
        return [NPC(npc, **self.parse_colors_tuples(data)) for (npc, data) in npc_data.items()]

    def parse_colors_tuples(self, data):
        if "color" in data:
            data["color"] = color.colors[data["color"]]
        for var in tuple_vars:
            if var in data:
                data[var] = [float(a) for a in data[var].split(", ")]
        return data