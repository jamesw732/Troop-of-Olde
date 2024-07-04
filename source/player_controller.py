"""Entirely private class (after instantiating) that handles player inputs."""

from ursina import *
import numpy
import json

from .character import Character
from .ui.main import ui
from .ui.items_window import ItemIcon


class PlayerController(Entity):
    """Client-side player input handler."""
    def __init__(self, character, peer=None, camdistance=20):
        """Initialize player controller."""
        super().__init__()
        self.character = character
        self.character.type = "player"

        self.peer = peer

        self.camdistance = camdistance

        self.focus = Entity(model="cube", visible_self=False, position=self.character.position + Vec3(0, 0.5 * self.character.height, 0), rotation=(1, 0, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.grounded_direction = Vec3(0, 0, 0)
        self.jumping_direction = Vec3(0, 0, 0)

        self.fix_player_namelabel()

        self.prev_mouse_position = mouse.position

        self.bind_keys()

    def update(self):
        """Continuous client updates"""
        # Frame by frame adjustments
        self.adjust_camera_zoom()
        self.adjust_focus()
        # Handle continuous inputs
        # Keyboard movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        movement_inputs = Vec3(strafe, 0, fwdback)
        self.handle_keyboard_movement(movement_inputs)
        # Keyboard rotation
        rotate_ud = held_keys['rotate_up'] - held_keys['rotate_down']
        rotate_lr = held_keys['rotate_right'] - held_keys['rotate_left']
        self.handle_keyboard_rotation(rotate_ud, rotate_lr)
        # Mouse rotation
        if held_keys['right mouse']:
            self.handle_mouse_rotation()

    def input(self, key):
        """Singular client updates"""
        if key == "jump":
            self.character.start_jump()
        if key == "scroll up":
            if mouse.hovered_entity and not mouse.hovered_entity.has_ancestor(camera.ui):
                self.camdistance = max(self.camdistance - 1, 0)
        if key == "scroll down":
            if mouse.hovered_entity and not mouse.hovered_entity.has_ancestor(camera.ui):
                self.camdistance = min(self.camdistance + 1, 75)
        if key == "right mouse down":
            # mouse.visible = False
            self.prev_mouse_position = mouse.position
        # if key == "right mouse up":
            # mouse.visible = True
        if key == "left mouse down":
            tgt = mouse.hovered_entity
            if isinstance(tgt, Character):
                self.set_target(tgt)
            elif isinstance(tgt, ItemIcon):
                tgt.clicked = True
                tgt.step = tgt.get_position(camera.ui) - mouse.position
        if key == "toggle_combat":
            msg = "Now entering combat" if not self.character.in_combat else "Now leaving combat"
            ui.gamewindow.add_message(msg)
            self.character.in_combat = not self.character.in_combat

    def handle_keyboard_movement(self, movement_inputs):
        """Sets keyboard component of character velocity.
        See Character.velocity_components.

        movement_inputs: Vec3"""
        if movement_inputs == Vec3(0, 0, 0):
            self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        else:
            theta = numpy.radians(-1 * self.character.rotation_y)
            rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
            move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
            move_direction = Vec3(move_direction[0], 0, move_direction[1]).normalized()
            self.character.velocity_components["keyboard"] = move_direction * self.character.speed

    def handle_keyboard_rotation(self, updown_rotation, leftright_rotation):
        """Handles rotation from keys "a", "d", "up arrow", "down arrow"."""
        # Keyboard Rotation
        # Slow down left/right rotation by multiplying by cos(x rotation)
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x))
                           * time.dt * 150, 0))
        self.focus.rotate((updown_rotation * time.dt * 150, 0, 0))
        self.fix_camera_rotation()

    def handle_mouse_rotation(self):
        """Handles rotation from right clicking and dragging the mouse."""
        # Mouse rotation:
        diff = mouse.position - self.prev_mouse_position
        vel = Vec3(-1 * diff[1], diff[0] * numpy.cos(numpy.radians(self.focus.rotation_x)), 0)
        self.focus.rotate(vel * 200)
        self.prev_mouse_position = mouse.position
        self.fix_camera_rotation()

    def fix_camera_rotation(self):
        """Handles all the problems that results from the camera rotating.
        Caps vertical rotation, removes z rotation, rotates character."""
        max_vert_rotation = 80
        self.focus.rotation_z = 0
        self.character.rotation_y = self.focus.rotation_y
        if self.focus.rotation_x > max_vert_rotation:
            self.focus.rotation_x = max_vert_rotation
        if self.focus.rotation < -max_vert_rotation:
            self.focus.rotation_x = -max_vert_rotation

    def adjust_camera_zoom(self):
        """Set camera zoom. Handles camera collision with entities"""
        theta = numpy.radians(90 - self.focus.rotation_x)
        phi = numpy.radians(-self.focus.rotation_y)
        direction = Vec3(numpy.sin(theta) * numpy.sin(phi), numpy.cos(theta), -1 * numpy.sin(theta) * numpy.cos(phi))
        ray = raycast(self.focus.position, direction=direction, distance=self.camdistance, ignore=self.character.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance

    def adjust_focus(self):
        """Called every frame, adjust player's focus to character's position"""
        self.focus.position = self.character.position + Vec3(0, 0.5 * self.character.height, 0)

    def fix_player_namelabel(self):
        """Hacky fix to player's namelabel being slow.
        Just make the parent of the namelabel the focus and that's it"""
        self.character.namelabel.parent = self.focus
        self.character.namelabel.position = Vec3(0, self.character.height, 0)
        self.character.namelabel.fix_rotation = lambda: None
        self.character.namelabel.fix_position = lambda: None

    def set_target(self, target):
        """Set character's target.

        target: Character"""
        self.character.target = target
        msg = f"Now targeting: {target.cname}"
        ui.gamewindow.add_message(msg)

    def bind_keys(self):
        """Load and read data/key_mappings.json and bind them in ursina.input_handler"""
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                input_handler.bind(k, v)