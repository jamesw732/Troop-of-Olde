"""Generate the world from a json. Only run by the server."""
from ursina import Entity, Sky, color
import json
import os

from .character import Character
from .states.state import State


class GenerateWorld:
    def __init__(self, file, headless=False):
        """Create world.

        file: str, name of file to load in data/zones. Not full path."""
        path = os.path.abspath(os.path.dirname(__file__))
        self.zones_path = os.path.join(path, "..", "data", "zones")
        zonepath = os.path.join(self.zones_path, file)
        self.headless = headless
        if "json" in zonepath:
            self.parse_json_zone(zonepath)

    def parse_json_zone(self, file):
        """Load the world by parsing a json

        file: str, name of file to load in data/zones. Not full path."""
        with open(file) as f:
            world_data = json.load(f)
        for (entity, data) in world_data.items():
            if entity == "Sky" and not self.headless:
                Sky(**data)
            else:
                Entity(**self.parse_colors(data))

    def create_npcs(self, file):
        """Spawn from the npc source file. Called only by server.

        file: str, name of file to load in data/zones. Not full path"""
        path = os.path.join(self.zones_path, file)
        with open(path) as f:
            npc_data = json.load(f)
        states = [(State("physical", data["physical"]),
                   State("base_combat", data["combat"]))
                   for (npc, data) in npc_data.items()]
        return [Character(pstate=tup[0], cbstate=tup[1]) for tup in states]

    def parse_colors(self, data):
        """Parses colors from a json, which are just formatted as strings.

        data: dict, probably returned by a json.load"""
        if "color" in data:
            data["color"] = color.colors[data["color"]]
        return data