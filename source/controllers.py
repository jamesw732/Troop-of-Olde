from ursina import *
import json

from .base import *
from .combat import *
from .gamestate import gs
from .physics import get_displacement, set_jump_vel, set_gravity_vel
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

        self.prev_mouse_position = mouse.position

        # The sequence number of movement inputs
        self.sequence_number = 0
        # The most recent relayed sequence number
        self.recv_sequence_number = 0
        # Current targets to lerp to
        self.target_pos = self.character.position
        self.target_rot = self.character.rotation_y
        self.mouse_y_rotation = 0
        # Previous positions/rotations to lerp from
        self.prev_pos = self.character.position
        self.prev_rot = self.character.rotation
        # Remember the position/rotation when we sent sequence numbers
        self.sn_to_pos = {}
        self.sn_to_rot = {}
        # Differences between what the server calculated and what we calculated at the most recently received
        # sequence number. Replaced with zeros for offsets smaller than some epsilon.
        self.rot_offset = 0
        # Timer used for interpolating between physics ticks
        self.predict_timer = 0
        # Amount of time it should take client to match server given no inputs
        self.offset_duration = 0.5

    def bind_character(self, character):
        self.character = character
        self.focus = Entity(
            parent=self.character,
            world_scale = (1, 1, 1),
            position = Vec3(0, 0.75, 0)
        )
        self.namelabel = NameLabel(character)
        self.fix_namelabel()
        # self.shadow = Entity(origin=(0, -0.5, 0), scale=self.character.scale, model='cube',
        #                      color=color.yellow, rotation=self.character.rotation,
        #                      position=self.character.position)

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
        # Predict position by interpolating between physics ticks
        self.predict_timer += time.dt
        pct = min(self.predict_timer / PHYSICS_UPDATE_RATE, 1)
        char.position = lerp(self.prev_pos, self.target_pos, pct)
        # Predict character y rotation, enforce camera x rotation
        char.rotation_y = lerp_angle(self.prev_rot, self.target_rot, pct)
        updown = held_keys['rotate_up'] - held_keys['rotate_down']
        self.focus.rotate(Vec3(updown * 100 * time.dt, 0, 0))
        if held_keys['right mouse']:
            mouse_rotation = self.get_mouse_rotation()
            self.focus.rotation_x += mouse_rotation[0]
            self.mouse_y_rotation += mouse_rotation[1]
        self.fix_camera_rotation()
        self.adjust_camera_zoom()
        # Client-side prediction for movement
        # pct = self.predict_timer / self.offset_duration
        # char.position += lerp(Vec3(0, 0, 0), self.pos_offset, pct)
        # char.rotation_y += lerp_angle(0, self.rot_offset, pct)
        # Performance: This probably doesn't need to happen every frame, just when we move.
        if char.get_on_gcd():
            char.tick_gcd()
        elif char.next_power is not None:
            # Client-side power queueing basically just waits to request to use the power
            power = char.next_power
            tgt = power.get_target()
            power.use()
            gs.network.peer.request_use_power(gs.network.server_connection, power.power_id)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        """Process movement inputs and send request to move to server.
        Update predicted physical state and reset lerp timer."""
        char = self.character
        # Keyboard Movement
        fwdback = held_keys['move_forward'] - held_keys['move_backward']
        strafe = held_keys['strafe_right'] - held_keys['strafe_left']
        keyboard_direction = Vec2(strafe, fwdback)
        # Keyboard Rotation
        rightleft = held_keys['rotate_right'] - held_keys['rotate_left']

        conn = gs.network.server_connection
        gs.network.peer.request_move(conn, self.sequence_number, keyboard_direction,
                                     rightleft, self.mouse_y_rotation)

        # Client-side prediction for movement/rotation
        char_speed = get_speed_modifier(char.speed)
        kb_vel = (char.right * strafe + char.forward * fwdback).normalized() * 10 * char_speed
        char.velocity_components["keyboard"] = kb_vel
        set_gravity_vel(char)
        set_jump_vel(char)
        displacement = get_displacement(char)
        # Store the previous/next target position for LERPING
        # Technically lagged behind by one step of PHYSICS_UPDATE_RATE
        self.prev_pos = char.position
        self.target_pos = char.position + displacement
        self.sn_to_pos[self.sequence_number] = self.target_pos
        # may need to mulyiply by math.cos(math.radians(self.focus.rotation_x)), 0)
        rotation = rightleft * 100 * PHYSICS_UPDATE_RATE + self.mouse_y_rotation
        self.prev_rot = self.target_rot
        self.target_rot = char.rotation_y + rotation + self.rot_offset
        self.sn_to_rot[self.sequence_number] = self.target_rot
        # Just some necessary bookkeeping things
        self.predict_timer = 0
        char.displacement_components["server_offset"] = Vec3(0, 0, 0)
        self.rot_offset = 0
        self.mouse_y_rotation = 0
        self.sequence_number += 1

    def get_mouse_rotation(self):
        """Handles rotation from right clicking and dragging the mouse."""
        # Mouse rotation:
        offset = mouse.position - self.prev_mouse_position
        self.prev_mouse_position = mouse.position
        vel = Vec3(-1 * offset[1], offset[0] * math.cos(math.radians(self.focus.rotation_x)), 0)
        return vel * 200

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
            gs.network.peer.request_jump(gs.network.server_connection)
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
        # Relayed back to client to determine where in history this state was updated, always use most recent
        self.sequence_number = 0

    def update(self):
        char = self.character
        if char.health <= 0:
            char.die()
        if char.target and not char.target.alive:
            char.target = None
            char.combat_timer = 0
        if char.target and char.target.alive and char.in_combat:
            mh_slot = slot_to_ind["mh"]
            mh = char.equipment[mh_slot]
            if tick_mh(char) and char.get_target_hittable(mh):
                hit, msg = attempt_attack(char, char.target, "mh")
                mh_skill = get_wpn_style(mh)
                if hit and check_raise_skill(char, mh_skill):
                    raise_skill(char, mh_skill)
                conn = gs.network.uuid_to_connection.get(char.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    # Should add some sort of check to make sure this isn't happening too often
                    gs.network.broadcast_cbstate_update(char.target)
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh_is_1h = not (mh is not None
                            and mh.type == "weapon"
                            and mh.info.get("style", "")[:2] == "2h")
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
            tgt = char.next_power.get_target()
            char.next_power.use(tgt)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        # Assumed that keyboard component gets set by a client
        set_gravity_vel(self.character)
        set_jump_vel(self.character)
        displacement = get_displacement(self.character)
        self.character.position += displacement
        self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        npc_pstate = State("physical", self.character)
        for conn in gs.network.peer.get_connections():
            if conn not in gs.network.connection_to_char:
                continue
            if self.character is gs.network.connection_to_char[conn]:
                gs.network.peer.update_target_attrs(conn, self.sequence_number, self.character.position,
                                                     self.character.rotation_y)
            else:
                gs.network.peer.update_lerp_pstate(conn, self.character.uuid, npc_pstate)


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