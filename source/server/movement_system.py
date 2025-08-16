from ursina import *

from .. import *


class MovementSystem(Entity):
    def __init__(self, global_containers):
        super().__init__()
        self.chars = global_containers.uuid_to_char.values()
        self.movement_states = global_containers.movement_states
        self.sequence_number = 0

    def add_char(self, char):
        """Add a MovementState

        Does not touch uuid_to_char"""
        self.movement_states[char.uuid] = MovementState()

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        for char in self.chars:
            self.tick_char_physics(char)

    def tick_char_physics(self, char):
        movement_state = self.movement_states[char.uuid]
        # Assumed that keyboard component gets set by a client
        set_gravity_vel(char)
        set_jump_vel(char)
        displacement = get_displacement(char)
        char.position += displacement
        char.velocity_components["keyboard"] = Vec3(0, 0, 0)
        # This executes client-side movement/rotation correct, to test movement without this
        # overhead, comment the rest of this function.
        for conn, uuid in network.connection_to_uuid.items():
            if char.uuid == uuid:
                network.peer.update_pc_lerp_attrs(
                    conn,
                    movement_state.sequence_number,
                    char.position,
                    char.rotation_y
                )
            else:
                network.peer.update_npc_lerp_attrs(
                    conn,
                    char.uuid,
                    char.position,
                    char.rotation_y
                )

    def handle_movement_inputs(self, char, sequence_number, kb_direction, kb_y_rotation, mouse_y_rotation):
        """Processes movement inputs from a client"""
        movement_state = self.movement_states[char.uuid]
        char_speed = get_speed_modifier(char.speed)
        vel = (char.right * kb_direction[0] + char.forward * kb_direction[1]).normalized() * 10 * char_speed
        if "keyboard" not in char.velocity_components:
            char.velocity_components["keyboard"] = vel
        char.velocity_components["keyboard"] += vel
        # char_rotation = Vec3(0, kb_y_rotation[1] * 100 * math.cos(math.radians(self.focus.rotation_x)), 0)
        y_rotation = kb_y_rotation * 100 * PHYSICS_UPDATE_RATE + mouse_y_rotation
        char.rotation_y += y_rotation
        # Will send back the most recently received sequence number to match the predicted state.
        # If packets arrive out of order, we want to update based on last sequence number
        if sequence_number > movement_state.sequence_number:
            movement_state.sequence_number = sequence_number
        # Update client's NPC animation
        if kb_direction != Vec2(0, 0) and movement_state.is_moving == False:
            movement_state.is_moving = True
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_start_run_anim(conn, char.uuid)
        elif kb_direction == Vec2(0, 0) and movement_state.is_moving == True:
            movement_state.is_moving = False
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_end_run_anim(conn, char.uuid)


class MovementState:
    def __init__(self):
        self.is_moving = False
        self.sequence_number = 0
