import json

from ursina import Entity, held_keys, every, Vec2
import ursina.input_handler

from ..base import PHYSICS_UPDATE_RATE
from ..gamestate import gs
from ..networking import network

class InputHandler(Entity):
    def __init__(self):
        super().__init__()

        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                ursina.input_handler.bind(k, v)

    def input(self, key):
        # This is temporary handling of logins when launching client from
        # main_multiplayer.py
        if not network.peer.is_running():
            if key == "c":
                print("Attempting to connect")
                network.peer.start("localhost", 8080, is_host=False)

    def update(self):
        ctrl = gs.playercontroller
        if ctrl is None:
            # Eventually, this class will depend on PlayerController and this check will
            # be deferred to PlayerController as a Character existence check
            return
        char = ctrl.character
        if char is None:
            return
        # Client-side movement/rotation updates
        updown_rot = held_keys['rotate_up'] - held_keys['rotate_down']
        ctrl.handle_updown_keyboard_rotation(updown_rot)
        if held_keys["right mouse"]:
            ctrl.handle_mouse_rotation()

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement_inputs(self):
        ctrl = gs.playercontroller
        if ctrl is None:
            # Eventually, this class will depend on PlayerController and this check will
            # be deferred to PlayerController as a Character existence check
            return
        char = ctrl.character
        if char is None:
            return
        # Send movement/rotation inputs to server
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        # Keyboard Rotation
        rightleft_rot = held_keys['rotate_right'] - held_keys['rotate_left']
        ctrl.update_movement_inputs(fwdback, strafe, rightleft_rot)
