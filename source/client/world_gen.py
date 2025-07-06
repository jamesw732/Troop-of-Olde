"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .. import data_path, get_npc_states_from_data


class ClientWorld:
    def __init__(self, file):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        self.zones_path = os.path.join(data_path, "zones")
        zonepath = os.path.join(self.zones_path, file)
        if "json" in zonepath:
            self.parse_json_zone(zonepath)

    def parse_json_zone(self, file):
        """Load the world by parsing a json

        file: str, name of file to load in data/zones. Not full path."""
        with open(file) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky":
                Sky(**data)
            else:
                Entity(**self.parse_colors(data))

    def parse_colors(self, data):
        """Parses colors from a json, which are just formatted as strings.

        data: dict, probably returned by a json.load"""
        if "color" in data:
            data["color"] = color.colors[data["color"]]
        return data