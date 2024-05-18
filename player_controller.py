"""Feeds player input into a character and its mob."""

from ursina import *
import numpy
from mob import Mob
from character import Character


class PlayerController(Entity):
    # For some reason, not inheriting Entity causes issues. Why? Can this be avoided?
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

    def update(self):
        self.character.velocity_components["keyboard"] = self.keyboard_vel()
        self.rotate_camera()
        self.adjust_camera_zoom()

        self.move_focus()

    def input(self, key):
        if key == "scroll down":
            self.camdistance = min(self.camdistance + 1, 150)
        if key == "scroll up":
            self.camdistance = max(self.camdistance - 1, 0)
        if key == "right mouse down":
            mouse.visible = False
            self.mouselock = mouse.position
        if key == "right mouse up":
            mouse.visible = True
        if key == "space":
            self.character.start_jump()
        if key == "left mouse down":
            tgt = mouse.hovered_entity
            if type(tgt) is Character:
                print(f"Now targeting: {tgt.name}")
                self.character.mob.target = tgt.mob
            else:
                self.character.mob.target = None
        if key == "1":
            print("Now entering combat" if not self.character.mob.in_combat else "Now leaving combat")
            self.character.mob.in_combat = not self.character.mob.in_combat

    def keyboard_vel(self):
        """Handle keyboard inputs for movement"""
        movement_inputs = Vec3(held_keys['e'] - held_keys['q'], 0, held_keys['w'] - held_keys['s']).normalized()
        theta = numpy.radians(-1 * self.character.rotation_y)
        rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
        move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
        move_direction = Vec3(move_direction[0], 0, move_direction[1])
        return move_direction * self.character.mob.speed

    def rotate_camera(self):
        """Handle keyboard/mouse inputs for camera"""
        # Keyboard Rotation:
        updown_rotation = held_keys["up arrow"] - held_keys["down arrow"]
        leftright_rotation = held_keys['d'] - held_keys['a']
        # Slow down left/right rotation by multiplying by cos(x rotation)
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x)), 0))
        self.focus.rotate((updown_rotation, 0, 0))

        max_vert_rotation = 80

        # Mouse rotation:
        if held_keys["right mouse"]:
            diff = mouse.position - self.mouselock
            vel = Vec3(-1 * diff[1], diff[0] * numpy.cos(numpy.radians(self.focus.rotation_x)), 0)
            self.focus.rotate(vel * 100)
            mouse.position = self.mouselock

        # Adjust everything
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

    def move_focus(self):
        """Called every frame, adjust player's focus to character's position"""
        self.focus.position = self.character.position + Vec3(0, 0.5 * self.character.height, 0)

    def make_name_text(self):
        Text(self.character.name, scale=15, parent=self.focus, origin=Vec3(0, 0, 0), position=Vec3(0, self.character.height, 0))