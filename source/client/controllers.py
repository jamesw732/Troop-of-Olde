from ursina import *

from .. import *


class PlayerController(Entity):
    """Controller for the player character.

    Handles client-side movement physics and interpolation, network updates.
    """
    def __init__(self, character):
        super().__init__()
        self.character = character
        # The sequence number of movement inputs
        self.sequence_number = 0
        # The most recent relayed sequence number
        self.recv_sequence_number = 0
        # Remember the position/rotation when we sent sequence numbers
        self.sn_to_pos = {}
        self.sn_to_rot = {}
        # Previous positions/rotations to lerp from
        self.prev_pos = self.character.position
        self.prev_rot = self.character.rotation_y
        # Current targets to lerp to
        self.target_pos = self.character.position
        self.target_rot = self.character.rotation_y
        # Components to build target rotation
        self.keyboard_y_rotation = 0
        self.mouse_y_rotation = 0
        self.rot_offset = 0 # Predicted difference from server's rotation
        # Timer used for interpolating position/rotation, counts up to PHYSICS_UPDATE_RATE
        self.predict_timer = 0

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

    def update_keyboard_inputs(self, fwdback, strafe, rightleft_rot):
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
        # Keyboard rotation
        self.keyboard_y_rotation = rightleft_rot
        # Server update
        conn = network.server_connection
        keyboard_direction = Vec2(strafe, fwdback)
        network.peer.request_move(conn, self.sequence_number, keyboard_direction,
                                     rightleft_rot, self.mouse_y_rotation)

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement(self):
        """Update target position/rotation on a fixed interval"""
        char = self.character
        if char is None:
            return
        # Client-side prediction for movement/rotation
        set_gravity_vel(char)
        displacement = get_displacement(char)
        # Update target position, lag behind by one timestep
        self.prev_pos = char.position
        self.target_pos = char.position + displacement
        self.sn_to_pos[self.sequence_number] = self.target_pos
        # Target rotation
        rotation = self.keyboard_y_rotation * 100 * PHYSICS_UPDATE_RATE + self.mouse_y_rotation
        self.prev_rot = self.target_rot
        self.target_rot = char.rotation_y + rotation + self.rot_offset
        self.sn_to_rot[self.sequence_number] = self.target_rot
        # Just some necessary bookkeeping things
        self.predict_timer = 0
        char.displacement_components["server_offset"] = Vec3(0, 0, 0)
        self.rot_offset = 0
        self.mouse_y_rotation = 0
        self.sequence_number += 1

    def update_mouse_y_rotation(self, amt):
        """Updates self.mouse_y_rotation with rotation obtained from mouse movement

        Does not update the character's rotation directly, instead this
        quantity is stored cumulatively over one physics tick period, then
        used to determine the next target_rot."""
        self.mouse_y_rotation += amt

    def do_jump(self):
        if self.character is None:
            return
        self.character.start_jump()
        network.peer.request_jump(network.server_connection)

    def update_lerp_attrs(self, sequence_number, pos, rot):
        """Updates target pos/rot to resynchronize after client-side prediction

        Rename to: update_server_offset"""
        if sequence_number > self.recv_sequence_number:
            self.recv_sequence_number = sequence_number
            for num in self.sn_to_pos.copy():
                if num < sequence_number:
                    self.sn_to_pos.pop(num)
                    self.sn_to_rot.pop(num)
        else:
            # Always take the most recent sequence number
            # Alternatively, reject completely if it's old
            sequence_number = self.recv_sequence_number
        # Compute the offset amt for position
        # sn_to_pos is missing sequence_number on startup
        predicted_pos = self.sn_to_pos.get(sequence_number, pos)
        pos_offset = pos - predicted_pos
        self.character.displacement_components["server_offset"] = pos_offset
        # Compute the offset amt for rotation
        rot = rot % 360
        predicted_rot = self.sn_to_rot.get(sequence_number, rot)
        rot_offset = rot - predicted_rot
        self.rot_offset = rot_offset


class NPCController(Entity):
    """Controller for all client-side Characters besides the player character.

    To the client, anything besides the player character is an NPC. Even other players.
    Handles client-side updates and linearly interpolates for smoothness.
    Future: Handles animations."""
    def __init__(self, character):
        super().__init__()
        self.character = character
        self._init_lerp_attrs()

    def update(self):
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

    def update_lerp_attrs(self, time_received, pos, rot):
        self.prev_pos = self.target_pos
        self.target_pos = pos
        self.prev_rot = self.target_rot
        self.target_rot = rot
        if pos - self.prev_pos != Vec3(0, 0, 0) or rot - self.prev_rot != 0:
            self.lerping = True
            self.lerp_rate = time_received - self.prev_lerp_recv
            self.prev_lerp_recv = time_received
            self.lerp_timer = 0
            self.character.position = pos
            self.character.rotation_y = rot

