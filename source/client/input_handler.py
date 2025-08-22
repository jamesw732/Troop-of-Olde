import json

from ursina import Entity, held_keys, every, Vec2, Vec3, mouse, camera, math, time
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
        # Used for mouse rotation
        self.prev_mouse_position = mouse.position

    def input(self, key):
        # This is temporary handling of logins when launching client from
        # main_multiplayer.py
        if not network.peer.is_running():
            if key == "c":
                print("Attempting to connect")
                network.peer.start("localhost", 8080, is_host=False)
                return
        ctrl = world.gamestate.pc_ctrl
        if ctrl is None:
            return
        cam_ctrl = world.gamestate.cam_ctrl
        if cam_ctrl is None:
            return
        tgt = mouse.hovered_entity
        if key == "jump":
            ctrl.do_jump()
        elif key == "scroll up":
            if tgt is None or not tgt.has_ancestor(camera.ui):
                cam_ctrl.zoom_in()
        elif key == "scroll down":
            if tgt is None or not tgt.has_ancestor(camera.ui):
                cam_ctrl.zoom_out()
        elif key == "right mouse down":
            self.start_mouse_rotation()
        elif key == "toggle_combat":
            world.combat_manager.input_toggle_combat()
        elif key == "left mouse down":
            if isinstance(tgt, ClickBox):
                world.combat_manager.input_set_target(tgt.parent)
        elif key in power_key_to_slot:
            slot = power_key_to_slot[key]
            power = world.gamestate.pc.powers[slot]
            used_power = world.power_system.handle_power_input(power)
            if used_power:
                ui.actionbar.start_cd_animation()
                ui.bars.update_display()

    def update(self):
        """Performs per-frame input handling

        Includes keyboard/mouse rotation."""
        cam_ctrl = world.gamestate.cam_ctrl
        if cam_ctrl is None:
            return
        # Client-side movement/rotation updates
        updown_rot = held_keys['rotate_up'] - held_keys['rotate_down']
        cam_ctrl.handle_updown_keyboard_rotation(updown_rot, time.dt)
        if held_keys["right mouse"]:
            self.handle_mouse_rotation()

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement_inputs(self):
        """Performs fixed-timestep movement input handling"""
        ctrl = world.gamestate.pc_ctrl
        if ctrl is None:
            return
        # Send movement/rotation inputs to server
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        # Keyboard Rotation
        rightleft_rot = held_keys['rotate_right'] - held_keys['rotate_left']
        ctrl.update_keyboard_inputs(fwdback, strafe, rightleft_rot)
        animator = world.gamestate.uuid_to_anim[ctrl.character.uuid]
        # Start run animation
        if fwdback != 0 or strafe != 0:
            animator.start_run_cycle()
        else:
            animator.end_run_cycle()

    @every(POWER_UPDATE_RATE)
    def tick_queued_power(self):
        if world.power_system is None:
            return
        queued_power = world.power_system.queued_power
        if queued_power is None:
            return
        char = world.gamestate.pc
        if char is None:
            return
        if queued_power.on_cooldown or char.get_on_gcd():
            return
        world.power_system.use_power(queued_power)
        ui.actionbar.start_cd_animation()
        ui.bars.update_display()

    def start_mouse_rotation(self):
        self.prev_mouse_position = mouse.position

    def handle_mouse_rotation(self):
        offset = mouse.position - self.prev_mouse_position
        self.prev_mouse_position = mouse.position
        ctrl = world.gamestate.pc_ctrl
        cam_ctrl = world.gamestate.cam_ctrl
        vel = Vec3(-1 * offset[1], offset[0] * math.cos(math.radians(cam_ctrl.focus.rotation_x)), 0)
        mouse_rotation = vel * 200
        cam_ctrl.update_mouse_x_rotation(mouse_rotation[0])
        ctrl.update_mouse_y_rotation(mouse_rotation[1])
