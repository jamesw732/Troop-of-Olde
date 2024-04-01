# Handles all world generation.
from ursina import *
import json

class GenerateWorld:
    def __init__(self, file):
        if "json" in file:
            self.parse_json(file)

    def parse_json(self, file):
        tuple_vars = ["origin", "position", "world_position", "rotation", "world_rotation"]
        with open(file) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky":
                Sky(**data)
            else:
                data = world_data[entity]
                if "color" in data:
                    data["color"] = color.colors[data["color"]]
                for var in tuple_vars:
                    if var in data:
                        data[var] = [float(a) for a in data[var].split(", ")]
                Entity(**data)