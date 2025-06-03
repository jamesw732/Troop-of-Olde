from ursina import *
import json

from .base import *
from .combat import *
from .gamestate import gs
from .item import item_is_2h
from .physics import handle_movement
from .skills import *
from .states import *

class PlayerController(Entity):
    """Handles player inputs and eventually client-side interpolation"""
    def __init__(self, character=None):
        assert not gs.network.peer.is_hosting()
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
            parent=self.character,
            world_scale = (1, 1, 1),
            position = Vec3(0, 0.75, 0)
        )
        self.namelabel = NameLabel(character)
        self.fix_namelabel()

    def bind_camera(self):
        self.camdistance = 20

        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

    def fix_namelabel(self):
        """Simplify player character's namelabel"""
        self.namelabel.parent = self.focus
        self.namelabel.world_position = self.character.position + Vec3(0, self.character.height * 1.3, 0)

    def bind_keys(self):
        """Load and read data/key_mappings.json and bind them in ursina.input_handler"""
        with open("data/key_mappings.json") as keymap:
            keymap_json = json.load(keymap)
            for k, v in keymap_json.items():
                input_handler.bind(k, v)

    def update(self):
        char = self.character
        # Performance: This probably doesn't need to happen every frame, just when we move.
        if char.get_on_gcd():
            char.tick_gcd()
        elif char.next_power is not None:
            # Client-side power queueing basically just waits to request to use the power
            power = char.next_power
            tgt = power.get_target(gs.pc)
            power.client_use_power()
            gs.network.peer.request_use_power(gs.network.server_connection, power.power_id)

    @every(PHYSICS_UPDATE_RATE)
    def handle_movement_inputs(self):
        char = self.character
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        keyboard_direction = Vec2(strafe, fwdback)
        # Keyboard Rotation
        # updown = held_keys['rotate_up'] - held_keys['rotate_down']
        rightleft = held_keys['rotate_right'] - held_keys['rotate_left']
        # Mouse Rotation, figure this out later
        # if held_keys['right mouse']:
        #     self.handle_mouse_rotation()
        gs.network.peer.request_move(gs.network.server_connection, keyboard_direction, rightleft)

    def handle_keyboard_rotation(self, rotation):
        """Handles rotation from keys "a", "d", "up arrow", "down arrow"."""
        # Keyboard Rotation
        # Slow down left/right rotation by multiplying by cos(x rotation)
        rotation[1] = rotation[1] * math.cos(math.radians(self.focus.rotation_x))
        char_rotation = Vec3(0, rotation[1] * 100, 0)
        focus_rotation = Vec3(rotation[0] * 100, 0, 0)
        dt = PHYSICS_UPDATE_RATE
        self.character.rotate(char_rotation * dt)
        self.focus.rotate(focus_rotation * dt)

    def handle_mouse_rotation(self):
        """Handles rotation from right clicking and dragging the mouse."""
        # Mouse rotation:
        diff = mouse.position - self.prev_mouse_position
        vel = Vec3(-1 * diff[1], diff[0] * math.cos(math.radians(self.focus.rotation_x)), 0)
        char_rotation = Vec3(0, vel[1] * 200, 0)
        focus_rotation = Vec3(vel[0] * 200, 0, 0)
        self.character.rotate(char_rotation)
        self.focus.rotate(focus_rotation)
        self.prev_mouse_position = mouse.position

    def fix_camera_rotation(self):
        """Handles all the problems that results from the camera rotating.
        Caps vertical rotation, removes z rotation, rotates character."""
        max_vert_rotation = 80
        self.character.world_rotation_x = 0
        self.character.world_rotation_z = 0
        self.focus.world_rotation_z = 0
        self.focus.rotation_x = clamp(self.focus.rotation_x, -max_vert_rotation, max_vert_rotation)

    def adjust_camera_zoom(self):
        """Set camera zoom. Handles camera collision with entities"""
        direction = camera.world_position - self.focus.world_position
        ray = raycast(self.focus.world_position, direction=direction, distance=self.camdistance,
                      ignore=self.character.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.world_position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance

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
        elif key == "scroll down":
            if tgt is None:
                return
            if not tgt.has_ancestor(camera.ui):
                self.camdistance = min(self.camdistance + 1, 75)
        elif key == "right mouse down":
            self.prev_mouse_position = mouse.position
        elif key == "toggle_combat":
            gs.network.peer.request_toggle_combat(gs.network.server_connection)

    def set_target(self, target):
        """Set character's target.

        target: Character"""
        self.character.target = target
        gs.network.peer.request_set_target(gs.network.server_connection, target.uuid)

    def on_destroy(self):
        destroy(self.namelabel)
        del self.namelabel
        del self.character

class NPCController(Entity):
    """Handles everything about characters besides the PC on the client.
    
    Todo: LERPing"""
    def __init__(self, character):
        assert not gs.network.peer.is_hosting()
        super().__init__()
        self.bind_character(character)
        self._init_lerp_attrs()

    def bind_character(self, character):
        self.character = character
        self.namelabel = NameLabel(character)

    def update(self):
        self.namelabel.adjust_position()
        self.namelabel.adjust_rotation()

        if self.lerping and self.prev_state:
            self.lerp_timer += time.dt
            # If timer finished, just apply the new state
            if self.lerp_timer >= self.lerp_rate:
                self.lerping = False
                self.new_state.apply(self.character)
            # Otherwise, LERP normally
            else:
                self.position = lerp(self.prev_state.get("position", self.position),
                                     self.new_state.get("position", self.position),
                                     self.lerp_timer / self.lerp_rate)
                self.rotation = lerp(self.prev_state.get("rotation", self.rotation),
                                     self.new_state.get("rotation", self.rotation),
                                     self.lerp_timer / self.lerp_rate)
    
    def _init_lerp_attrs(self):
        """Initialize lerp logic"""
        self.prev_state = None
        self.new_state = State("physical", self)
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def update_lerp_state(self, state, time):
        """Essentially just increments the lerp setup.
        Slide prev and new state, set self.lerping = True, and apply old state"""
        self.prev_state = self.new_state
        self.new_state = state
        if self.prev_state:
            self.lerping = True
            self.lerp_rate = time - self.prev_lerp_recv
            self.prev_lerp_recv = time
            self.lerp_timer = 0
            # Apply old state to ensure synchronization and update non-lerp attrs
            self.prev_state.apply(self.character)

    def on_destroy(self):
        destroy(self.namelabel)
        del self.namelabel
        del self.character

class MobController(Entity):
    """Handles server-side character logic such as combat and (eventually)
    movement"""
    def __init__(self, character):
        assert gs.network.peer.is_hosting()
        super().__init__()
        self.character = character

    def update(self):
        char = self.character
        if char.health <= 0:
            char.die()
        if char.target and not char.target.alive:
            char.target = None
            char.combat_timer = 0
        if char.target and char.target.alive and char.in_combat:
            mh_slot = slot_to_ind["mh"]
            if tick_mh(char) and char.get_target_hittable(char.equipment[mh_slot]):
                hit, msg = attempt_attack(char, char.target, "mh")
                mh_skill = get_wpn_style(char.equipment[mh_slot])
                if hit and check_raise_skill(char, mh_skill):
                    raise_skill(char, mh_skill)
                conn = gs.network.uuid_to_connection.get(char.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    # Should add some sort of check to make sure this isn't happening too often
                    gs.network.broadcast_cbstate_update(char.target)
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh_is_1h = not item_is_2h(char.equipment[mh_slot])
            oh_slot = slot_to_ind["oh"]
            offhand = char.equipment[oh_slot]
            # basically just check if not wearing a shield
            dual_wielding =  mh_is_1h and (offhand is None or offhand.type == "weapon")
            if dual_wielding and tick_oh(char)\
            and char.get_target_hittable(char.equipment[oh_slot]):
                hit, msg = attempt_attack(char, char.target, "oh")
                oh_skill = get_wpn_style(char.equipment[oh_slot])
                if hit and check_raise_skill(char, oh_skill):
                    raise_skill(char, oh_skill)
                conn = gs.network.uuid_to_connection.get(char.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    gs.network.broadcast_cbstate_update(char.target)
        else:
            char.mh_combat_timer = 0
            char.oh_combat_timer = 0
        if char.get_on_gcd():
            char.tick_gcd()
        elif char.next_power is not None:
            tgt = char.next_power.get_target(char)
            char.next_power.use(char, tgt)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        handle_movement(self.character)
        pstate = State("physical", src=self.character)
        for conn in gs.network.peer.get_connections():
            # For other clients, this should be update_lerp_pstate
            gs.network.peer.update_pstate(conn, self.character.uuid, pstate)


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