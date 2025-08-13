import json

from ursina import Entity, held_keys, every, Vec2, mouse, camera
import ursina.input_handler

from .character import ClickBox
from .ui import ui
from .world import world
from .. import PHYSICS_UPDATE_RATE, POWER_UPDATE_RATE, network, power_key_to_slot

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
                return
        ctrl = world.pc_ctrl
        if ctrl is None:
            return
        tgt = mouse.hovered_entity
        if key == "jump":
            ctrl.do_jump()
        elif key == "scroll up":
            if tgt is None or not tgt.has_ancestor(camera.ui):
                ctrl.zoom_in()
        elif key == "scroll down":
            if tgt is None or not tgt.has_ancestor(camera.ui):
                ctrl.zoom_out()
        elif key == "right mouse down":
            ctrl.start_mouse_rotation()
        elif key == "toggle_combat":
            ctrl.toggle_combat()
        elif key == "left mouse down":
            if isinstance(tgt, ClickBox):
                ctrl.set_target(tgt.parent)
        elif key in power_key_to_slot:
            slot = power_key_to_slot[key]
            power = world.pc.powers[slot]
            used_power = world.power_system.handle_power_input(power)
            if used_power:
                ui.actionbar.start_cd_animation()
                ui.bars.update_display()

    def update(self):
        """Performs per-frame input handling

        Includes keyboard/mouse rotation."""
        ctrl = world.pc_ctrl
        if ctrl is None:
            return
        # Client-side movement/rotation updates
        updown_rot = held_keys['rotate_up'] - held_keys['rotate_down']
        ctrl.handle_updown_keyboard_rotation(updown_rot)
        if held_keys["right mouse"]:
            ctrl.handle_mouse_rotation()

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement_inputs(self):
        """Performs fixed-timestep movement input handling"""
        ctrl = world.pc_ctrl
        if ctrl is None:
            return
        # Send movement/rotation inputs to server
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        # Keyboard Rotation
        rightleft_rot = held_keys['rotate_right'] - held_keys['rotate_left']
        ctrl.update_movement_inputs(fwdback, strafe, rightleft_rot)

    @every(POWER_UPDATE_RATE)
    def tick_queued_power(self):
        if world.power_system is None:
            return
        queued_power = world.power_system.queued_power
        if queued_power is None:
            return
        char = world.pc
        if char is None:
            return
        if queued_power.on_cooldown or char.get_on_gcd():
            return
        world.power_system.use_power(queued_power)
        ui.actionbar.start_cd_animation()
        ui.bars.update_display()
