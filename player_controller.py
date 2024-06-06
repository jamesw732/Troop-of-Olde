from ursina import *
import numpy
from mob import Mob
from character import Character
import json


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

    def update(self):
        # Keep strictly client-only things that are updated frame by frame in here.
        self.adjust_camera_zoom()
        self.move_focus()

    def handle_player_inputs(self, input_state):
        """Respond to PlayerInput.input_state dict"""
        movement_inputs = Vec3(input_state.get("strafe", 0), 0, input_state.get("move", 0)).normalized()
        self.keyboard_vel(movement_inputs)
        rotation_inputs = (input_state.get("rotate_ud", 0), input_state.get("rotate_lr", 0))
        self.keyboard_rot(*rotation_inputs)

        if input_state.get("jump"):
            self.character.start_jump()
        if input_state.get("zoom_in"):
            self.camdistance = max(self.camdistance - 1, 0)
        if input_state.get("zoom_out"):
            self.camdistance = min(self.camdistance + 1, 75)
        if input_state.get("start_drag_rotate"):
            mouse.visible = False
            self.mouselock_position = mouse.position
        if input_state.get("end_drag_rotate"):
            mouse.visible = True
        if input_state.get("drag_rotating"):
            self.drag_rot()
        if input_state.get("target"):
            self.set_target(input_state.get("target"))
        if input_state.get("toggle_combat"):
            print("Now entering combat" if not self.character.mob.in_combat else "Now leaving combat")
            self.character.mob.in_combat = not self.character.mob.in_combat

    def keyboard_vel(self, movement_inputs):
        """Handle keyboard inputs for movement"""
        if movement_inputs == Vec3(0, 0, 0):
            self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        else:
            theta = numpy.radians(-1 * self.character.rotation_y)
            rotation_matrix = numpy.array([[numpy.cos(theta), -1 * numpy.sin(theta)], [numpy.sin(theta), numpy.cos(theta)]])
            move_direction = rotation_matrix @ numpy.array([movement_inputs[0], movement_inputs[2]])
            move_direction = Vec3(move_direction[0], 0, move_direction[1])
            self.character.velocity_components["keyboard"] = move_direction * self.character.speed

    def keyboard_rot(self, updown_rotation, leftright_rotation):
        # Keyboard Rotation
        # Slow down left/right rotation by multiplying by cos(x rotation)
        self.focus.rotate((0, leftright_rotation * numpy.cos(numpy.radians(self.focus.rotation_x)), 0))
        self.focus.rotate((updown_rotation, 0, 0))
        self.fix_camera_rotation()

    def drag_rot(self):
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

    def move_focus(self):
        """Called every frame, adjust player's focus to character's position"""
        self.focus.position = self.character.position + Vec3(0, 0.5 * self.character.height, 0)

    def make_name_text(self):
        Text(self.character.name, scale=15, parent=self.focus, origin=Vec3(0, 0, 0), position=Vec3(0, self.character.height, 0))

    def set_target(self, target):
        self.character.mob.target = target.mob
        print(f"Now targeting: {target.name}")


class PlayerInput(Entity):
    """Parse player inputs, send to player_controller.
    If online, reroute to host, then to player controller. Host computes new state diff, sends to all clients."""
    def __init__(self, player_controller):
        super().__init__()
        self.player_controller = player_controller
        self.input_state = {}
        self.bind_keys()

    def update(self):
        """Take continuous inputs"""
        # Probably don't need to do this whole dict nonsense for the continuous inputs.
        # We won't be sending these inputs across the server, will just send a state update
        # every .1 seconds or so.
        self.input_state["move"] = held_keys['move_forward'] - held_keys['move_backward']
        self.input_state["strafe"] = held_keys['strafe_right'] - held_keys['strafe_left']
        self.input_state["rotate_ud"] = held_keys['rotate_up'] - held_keys['rotate_down']
        self.input_state["rotate_lr"] = held_keys['rotate_right'] - held_keys['rotate_left']
        self.input_state["drag_rotating"] = held_keys['right mouse']
        # No need to send false-y inputs, if coded properly these should always do nothing
        self.filter_input_state()
        # Eventually, serialize input state and send to host. Currently, just pass into player controller
        self.player_controller.handle_player_inputs(self.input_state)
        # Clear input state for next frame
        self.input_state.clear()

    def input(self, key):
        # This should be the only input function in the entire repo, hopefully
        if key == "jump":
            self.input_state["jump"] = 1
        # These checks will grow in sophistication as the client becomes more complicated
        # I.E. Scrolling up might mean zooming in, but it might also mean scrolling up in the chat window
        if key == "scroll up":
            self.input_state["zoom_in"] = 1
        if key == "scroll down":
            self.input_state["zoom_out"] = 1
        if key == "right mouse down":
            self.input_state["start_drag_rotate"] = 1
        if key == "right mouse up":
            self.input_state["end_drag_rotate"] = 1
        if key == "left mouse down":
            tgt = mouse.hovered_entity
            if type(tgt) is Character:
                self.input_state["target"] = tgt
        if key == "toggle_combat":
            self.input_state["toggle_combat"] = 1

    def bind_keys(self):
        # Read json
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                input_handler.bind(k, v)

    def filter_input_state(self):
        self.input_state = {k: v for k, v in self.input_state.items() if v}