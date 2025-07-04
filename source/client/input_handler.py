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

        # Power queueing is essentially a delayed input
        if not char.get_on_gcd() and char.next_power is not None and not char.next_power.on_cooldown:
            # Client-side power queueing basically just waits to request to use the power
            power = char.next_power
            tgt = power.get_target()
            power.use()
            gs.network.peer.request_use_power(gs.network.server_connection, power.power_id)

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement(self):
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
        keyboard_direction = Vec2(strafe, fwdback)
        # Keyboard Rotation
        rightleft_rot = held_keys['rotate_right'] - held_keys['rotate_left']

        conn = gs.network.server_connection
        gs.network.peer.request_move(conn, ctrl.sequence_number, keyboard_direction,
                                     rightleft_rot, ctrl.mouse_y_rotation)
        # Predict movement/rotation updates client-side
        ctrl.update_keyboard_velocity(fwdback, strafe)
        ctrl.update_target_rotation(rightleft_rot)
