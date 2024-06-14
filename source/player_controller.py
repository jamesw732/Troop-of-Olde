from ursina import *
import numpy
import json

from .mob import Mob
from .character import Character


class PlayerController(Entity):
    """Client-side player input handler."""
    def __init__(self, character, camdistance=20):
        """Initialize player controller."""
        super().__init__()
        self.character = character
        self.camdistance = camdistance

        self.focus = Entity(model="cube", visible_self=False, position=self.character.position + Vec3(0, 0.5 * self.character.height, 0), rotation=(1, 0, 0))
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

        self.grounded_direction = Vec3(0, 0, 0)
        self.jumping_direction = Vec3(0, 0, 0)

        self.character.namelabel = self.make_name_text()

        self.mouselock_position = mouse.position

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
            self.camdistance = max(self.camdistance - 1, 0)
        if key == "zoom_out":
            self.camdistance = min(self.camdistance + 1, 75)
        if key == "right mouse down":
            mouse.visible = False
            self.mouselock_position = mouse.position
        if key == "right mouse up":
            mouse.visible = True
        if key == "left mouse down":
            tgt = mouse.hovered_entity
            if type(tgt) is Character:
                self.set_target(tgt)
        if key == "toggle_combat":
            print("Now entering combat" if not self.character.mob.in_combat else "Now leaving combat")
            self.character.mob.in_combat = not self.character.mob.in_combat

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
        # Keyboard Rotation
        # Slow down left/right rotation by multiplying by cos(x rotation)
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x)), 0))
        self.focus.rotate((updown_rotation, 0, 0))
        self.fix_camera_rotation()

    def handle_mouse_rotation(self):
        # Mouse rotation:
        diff = mouse.position - self.mouselock_position
        vel = Vec3(-1 * diff[1], diff[0] * numpy.cos(numpy.radians(self.focus.rotation_x)), 0)
        self.focus.rotate(vel * 100)
        mouse.position = self.mouselock_position
        self.fix_camera_rotation()

    def fix_camera_rotation(self):
        # Adjust everything
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

    def make_name_text(self):
        Text(self.character.name, scale=15, parent=self.focus, origin=Vec3(0, 0, 0), position=Vec3(0, self.character.height, 0))

    def set_target(self, target):
        self.character.mob.target = target.mob
        print(f"Now targeting: {target.name}")

    def bind_keys(self):
        # Bind keys based on key_mappings.json
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                input_handler.bind(k, v)