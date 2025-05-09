from ursina import *
import numpy
import json

from .gamestate import gs
from .physics import handle_movement

class PlayerController(Entity):
    """Handles player inputs and eventually client-side interpolation"""
    def __init__(self, character=None):
        super().__init__()
        if character is not None:
            self.bind_character(character)
        else:
            self.character = None
        self.bind_camera()
        self.bind_keys()

        self.prev_mouse_posiiton = mouse.position

    def bind_character(self, character):
        self.character = character
        self.focus = Entity(
            visible_self=False,
            position=self.character.position
                + Vec3(0, 0.5 * self.character.height),
            rotation = (1, 0, 0))
        self.namelabel = NameLabel(character)
        self.fix_namelabel()

    def bind_camera(self):
        self.camdistance = 20

        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

    def fix_namelabel(self):
        """Simplify player character's namelabel"""
        self.namelabel.parent = self.focus
        self.namelabel.position = Vec3(0, self.character.height, 0)
        # self.character.namelabel.fix_rotation = lambda: None
        # self.character.namelabel.fix_position = lambda: None

    def bind_keys(self):
        """Load and read data/key_mappings.json and bind them in ursina.input_handler"""
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                input_handler.bind(k, v)

    def update(self):
        # Performance: This probably doesn't need to happen every frame, just when we move.
        self.adjust_camera_zoom()
        self.adjust_focus()

        # Performance: probably don't need to use numpy here, just use 
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        movement_inputs = Vec3(strafe, 0, fwdback)
        self.handle_keyboard_movement(movement_inputs)
        # Keyboard Rotation
        rotate_ud = held_keys['rotate_up'] - held_keys['rotate_down']
        rotate_lr = held_keys['rotate_right'] - held_keys['rotate_left']
        self.handle_keyboard_rotation(rotate_ud, rotate_lr)
        # Mouse Rotation
        if held_keys['right mouse']:
            self.handle_mouse_rotation()

    def input(self, key):
        """Updates from single client inputs"""
        tgt = mouse.hovered_entity
        if key == "jump":
            self.character.start_jump()
        elif key == "scroll up":
            if tgt is None:
                return
            if not tgt.has_ancestor(camera.ui):
                self.camdistance = max(self.camdistance - 1, 0)
            if tgt.has_ancestor(gs.ui.gamewindow.parent):
                gs.ui.gamewindow.scrollbar.scroll_up()
        elif key == "scroll down":
            if tgt is None:
                return
            if not tgt.has_ancestor(camera.ui):
                self.camdistance = min(self.camdistance + 1, 75)
            if tgt.has_ancestor(gs.ui.gamewindow.parent):
                gs.ui.gamewindow.scrollbar.scroll_down()
        elif key == "right mouse down":
            self.prev_mouse_position = mouse.position
        elif key == "toggle combat":
            gs.network.peer.request_toggle_combat(gs.network.server_connection)
        elif key in gs.ui.playerwindow.input_to_interface:
            gs.ui.playerwindow.open_window(key)

    def adjust_camera_zoom(self):
        """Set camera zoom. Handles camera collision with entities"""
        theta = numpy.radians(90 - self.focus.rotation_x)
        phi = numpy.radians(-self.focus.rotation_y)
        direction = Vec3(numpy.sin(theta) * numpy.sin(phi), numpy.cos(theta),
                         -1 * numpy.sin(theta) * numpy.cos(phi))
        ray = raycast(self.focus.position, direction=direction, distance=self.camdistance,
                      ignore=self.character.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance

    def adjust_focus(self):
        """Called every frame, adjust player's focus to character's position"""
        self.focus.position = self.character.position + Vec3(0, 0.5 * self.character.height, 0)

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
            self.character.velocity_components["keyboard"] = move_direction * (12 * (1 + self.character.speed / 100))

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

    def set_target(self, target):
        """Set character's target.

        target: Character"""
        self.character.target = target
        gs.network.peer.request_set_target(gs.network.server_connection, target.uuid)


class NPCController(Entity):
    """Handles everything about characters besides the PC on the client."""
    def __init__(self, character=None):
        if character is not None:
            self.bind_character(character)
        else:
            self.character = None

    def bind_character(self, character):
        self.character = character
        self.namelabel = NameLabel(character)

    def update(self):
        if self.character:
            self.namelabel.adjust_position()
            self.namelabel.adjust_rotation()

class MobController(Entity):
    """Handles NPC AI logic and stuff like that on the server"""
    def __init__(self, character=None):
        pass

# class ServerPlayerController(Entity):
#     def __inif__(self):
#         pass

# class ServerNPCController(Entity):
#     def __init__(self):
#         pass

class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character
        
        Todo: Change parent to character"""
        super().__init__(char.cname, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def adjust_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if gs.pc:
            direction = gs.pc.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def adjust_position(self):
        """Position the namelabel above the character"""
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)