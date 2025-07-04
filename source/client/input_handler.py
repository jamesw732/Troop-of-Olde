import json

from ursina import Entity
import ursina.input_handler

from ..gamestate import gs
from ..networking import network

class InputHandler(Entity):
    def __init__(self):
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                ursina.input_handler.bind(k, v)

    def input(self, key):
        if not network.peer.is_running():
            if key == "c":
                print("Attempting to connect")
                network.peer.start("localhost", 8080, is_host=False)
