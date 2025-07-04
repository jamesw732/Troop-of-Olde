"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from ..base import data_path
from .character import ServerCharacter
from ..states import get_npc_states_from_data


class ServerWorld:
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
                continue
            Entity(**self.parse_colors(data))

    def create_npcs(self, file):
        """Spawn from the npc source file. Called only by server.

        file: str, name of file to load in data/zones. Not full path"""
        path = os.path.join(self.zones_path, file)
        with open(path) as f:
            npc_data = json.load(f)
        return [ServerCharacter(**get_npc_states_from_data(data, name))
                                for name, data in npc_data.items()]

    def parse_colors(self, data):
        """Parses colors from a json, which are just formatted as strings.

        data: dict, probably returned by a json.load"""
        if "color" in data:
            data["color"] = color.colors[data["color"]]
        return data