"""Controllers objects attached to Characters which serve as the bridge between inputs
and the game engine/logic API. Functionality is split between client-side player characters,
client-side NPCs, and server-side Characters.
"""
from ursina import *

from .. import *


class PlayerController(Entity):
    """Controller for the player character.

    Handles client-side physics and interpolation, network updates.
    """
    def __init__(self, character=None, on_destroy=lambda: None):
        super().__init__()
        if character is not None:
            self.character = character
            self.focus = Entity(
                parent=self.character,
                world_rotation_y=0,
                world_scale = (1, 1, 1),
                position = Vec3(0, 0.75, 0)
            )
            self.namelabel = NameLabel(character)
            self.namelabel.parent = self.focus
            self.namelabel.world_position = self.character.position + Vec3(0, self.character.height * 1.3, 0)
            # self.shadow = Entity(origin=(0, -0.5, 0), scale=self.character.scale, model='cube',
            #                      color=color.yellow, rotation=self.character.rotation,
            #                      position=self.character.position)
        else:
            self.character = None
            self.focus = None
        self.on_destroy=on_destroy
        # Bind camera
        self.camdistance = 20
        camera.parent = self.focus
        camera.position = (0, 0, -1 * self.camdistance)

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

    def update(self):
        char = self.character
        # Predict position by interpolating between physics ticks
        self.predict_timer += time.dt
        pct = min(self.predict_timer / PHYSICS_UPDATE_RATE, 1)
        char.position = lerp(self.prev_pos, self.target_pos, pct)
        # Predict character y rotation, enforce camera x rotation
        char.rotation_y = lerp_angle(self.prev_rot, self.target_rot, pct)
        # Fix character rotation
        self.character.rotation_x = 0
        self.character.rotation_z = 0
        self.focus.rotation_z = 0
        max_vert_rotation = 80
        self.focus.rotation_x = clamp(self.focus.rotation_x, -max_vert_rotation, max_vert_rotation)
        # Adjust camera zoom
        direction = camera.world_position - self.focus.world_position
        ray = raycast(self.focus.world_position, direction=direction, distance=self.camdistance,
                      ignore=self.character.ignore_traverse)
        if ray.hit:
            dist = math.dist(ray.world_point, self.focus.world_position)
            camera.z = -1 * min(self.camdistance, dist)
        else:
            camera.z = -1 * self.camdistance
        if char.get_on_gcd():
            char.tick_gcd()
        elif char.next_power is not None and not char.next_power.on_cooldown:
            self.use_power(char.next_power)

    def handle_power_input(self, power):
        """Performs the operations caused by entering a power input.

        If not on cooldown, use the power. If on cooldown, queue the power"""
        if self.character.get_on_gcd() or power.on_cooldown:
            if self.character.next_power is power:
                # Attempted to queue an already queued power, just remove it
                self.character.next_power = None
            else:
                # Queued power will be used once off cooldown
                power.queue(self.character)
        else:
            self.use_power(power)

    def use_power(self, power):
        tgt = power.get_target(self.character)
        if tgt is None:
            return
        if self.character.energy < power.cost:
            return
        power.use(self.character, tgt)
        network.peer.request_use_power(network.server_connection, power.power_id)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        """Process movement inputs and send request to move to server.
        Update predicted physical state and reset lerp timer."""
        char = self.character
        if char is None:
            return
        # Client-side prediction for movement/rotation
        set_gravity_vel(char)
        set_jump_vel(char)
        displacement = get_displacement(char)
        # Store the previous/next target position for LERPING
        # Technically lagged behind by one step of PHYSICS_UPDATE_RATE
        self.prev_pos = char.position
        self.target_pos = char.position + displacement
        self.sn_to_pos[self.sequence_number] = self.target_pos
        # Just some necessary bookkeeping things
        self.predict_timer = 0
        char.displacement_components["server_offset"] = Vec3(0, 0, 0)
        self.rot_offset = 0
        self.mouse_y_rotation = 0
        self.sequence_number += 1

    def update_movement_inputs(self, fwdback, strafe, rightleft_rot):
        """Update local keyboard velocity and target rotation, send
        request for server to do the same

        Performed at the end of the frame, and relies on handle_mouse_rotation
        to correctly update target_rot according to mouse rotation."""
        # Local updates
        char = self.character
        # Keyboard velocity
        char_speed = get_speed_modifier(char.speed)
        kb_vel = (char.right * strafe + char.forward * fwdback).normalized() * 10 * char_speed
        char.velocity_components["keyboard"] = kb_vel
        # Target rotation
        rotation = rightleft_rot * 100 * PHYSICS_UPDATE_RATE + self.mouse_y_rotation
        self.prev_rot = self.target_rot
        self.target_rot = char.rotation_y + rotation + self.rot_offset
        self.sn_to_rot[self.sequence_number] = self.target_rot
        # Server update
        conn = network.server_connection
        keyboard_direction = Vec2(strafe, fwdback)
        network.peer.request_move(conn, self.sequence_number, keyboard_direction,
                                     rightleft_rot, self.mouse_y_rotation)

    def handle_updown_keyboard_rotation(self, updown):
        """Handles up/down arrow key rotation.

        Only affects up-down rotation, which is irrelevant to server,
        so nothing sent to server."""
        self.focus.rotate(Vec3(updown * 100 * time.dt, 0, 0))

    def start_mouse_rotation(self):
        self.prev_mouse_position = mouse.position

    def handle_mouse_rotation(self):
        """Updates self.mouse_y_rotation according to mouse rotation.

        Does not update the character's rotation directly, instead this
        quantity is stored cumulatively over one physics tick period, then
        used to determine the next target_rot."""
        offset = mouse.position - self.prev_mouse_position
        self.prev_mouse_position = mouse.position
        vel = Vec3(-1 * offset[1], offset[0] * math.cos(math.radians(self.focus.rotation_x)), 0)
        mouse_rotation = vel * 200
        self.focus.rotation_x += mouse_rotation[0]
        self.mouse_y_rotation += mouse_rotation[1]

    def do_jump(self):
        if self.character is None:
            return
        self.character.start_jump()
        network.peer.request_jump(network.server_connection)

    def zoom_in(self):
        self.camdistance = max(self.camdistance - 1, 0)

    def zoom_out(self):
        self.camdistance = min(self.camdistance + 1, 75)

    def set_target(self, target):
        """Set character's target.

        target: Character"""
        self.character.target = target
        network.peer.request_set_target(network.server_connection, target.uuid)

    def toggle_combat(self):
        network.peer.request_toggle_combat(network.server_connection)

    def kill(self):
        """Clean up character upon death"""
        # also need to clear enemy targets
        self.character.alive = False
        del self.character.ignore_traverse
        destroy(self.character)
        self.character = None
        # del self.character
        destroy(self.namelabel)
        del self.namelabel.char
        del self.namelabel
        # del self.namelabel
        destroy(self.focus)
        del self.focus
        destroy(self)


class NPCController(Entity):
    """Controller for all client-side Characters besides the player character.

    To the client, anything besides the player character is an NPC. Even other players.
    Handles client-side updates and linearly interpolates for smoothness.
    Future: Handles animations."""
    def __init__(self, character, on_destroy=lambda: None):
        super().__init__()
        self.character = character
        self.namelabel = NameLabel(character)
        self._init_lerp_attrs()
        self.on_destroy = on_destroy

    def update(self):
        self.namelabel.adjust_position()
        self.namelabel.adjust_rotation()
        # Lerp attrs updated by network.peer.update_npc_lerp_attrs
        if self.lerping:
            self.lerp_timer += time.dt
            # If timer finished, just apply the new attrs
            if self.lerp_timer >= self.lerp_rate:
                self.lerping = False
                self.character.position = self.target_pos
                self.character.rotation_y = self.target_rot
            # Otherwise, LERP normally
            else:
                pct = self.lerp_timer / self.lerp_rate
                self.character.position = lerp(self.prev_pos, self.target_pos, pct)
                self.character.rotation_y = lerp_angle(self.prev_rot, self.target_rot, pct)
    
    def _init_lerp_attrs(self):
        """Initialize lerp logic"""
        self.prev_pos = Vec3(0, 0, 0)
        self.prev_rot = 0
        self.target_pos = Vec3(0, 0, 0)
        self.target_rot = 0
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def kill(self):
        """Clean up character upon death"""
        self.character.alive = False
        del self.character.ignore_traverse
        destroy(self.character)
        del self.character
        destroy(self.namelabel)
        del self.namelabel.char
        del self.namelabel
        destroy(self)


class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character
        
        Todo: Change parent to character"""
        super().__init__(char.cname, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def adjust_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if self.char.position:
            direction = self.char.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def adjust_position(self):
        """Position the namelabel above the character"""
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)