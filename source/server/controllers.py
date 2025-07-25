"""Controllers objects attached to Characters which serve as the bridge between inputs
and the game engine/logic API. Functionality is split between client-side player characters,
client-side NPCs, and server-side Characters.
"""
from ursina import *
import json

from .. import *


class MobController(Entity):
    """Controller for all server-side characters.

    Handles server-side combat and physics.
    Does not, and will not, handle NPC logic such as pathing, aggression, etc.
    These will instead be handled by an NPCLogic (tentative name) class which reads the
    game state and makes "inputs" to be processed by this class. These "inputs" should be
    compatible with the processed outputs sent by PlayerController.
    """
    def __init__(self, character, on_destroy=lambda: None):
        assert network.peer.is_hosting()
        super().__init__()
        self.character = character
        self.on_destroy=on_destroy
        # Relayed back to client to determine where in history this state was updated, always use most recent
        self.sequence_number = 0
        self.moving = False

    def update(self):
        char = self.character
        # Death handling
        if char.health <= 0:
            self.kill()
            return
        # Combat handling
        if not char.target or not char.target.alive:
            char.target = None
            char.mh_combat_timer = 0
            char.oh_combat_timer = 0
        elif char.in_combat:
            hit_mh = self.handle_combat("mh")
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh = char.equipment[slot_to_ind["mh"]]
            mh_is_1h = mh is None or mh.info.get("style", "")[:2] != "2h"
            hit_oh = False
            if mh_is_1h:
                hit_oh = self.handle_combat("oh")
            if hit_mh or hit_mh:
                network.broadcast_cbstate_update(char.target)
        # Queued power handling
        if char.get_on_gcd():
            char.tick_gcd()
        self.handle_effects()
        # Need to update 

    def handle_combat(self, slot):
        src = self.character
        tgt = src.target
        src_conn = network.uuid_to_connection.get(src.uuid, None)
        tgt_conn = network.uuid_to_connection.get(tgt.uuid, None)
        idx = slot_to_ind[slot]
        wpn = src.equipment[idx]
        # Check whether to attempt to perform an attack or not
        attempting = tick_combat_timer(src, slot, wpn)
        if not attempting:
            return False
        for conn in network.connection_to_uuid:
            network.peer.remote_do_attack_anim(conn, src.uuid, slot)
        # Check whether target his within range and in line of sight
        hittable, msg = get_target_hittable(src, wpn)
        if not hittable:
            if src_conn is not None:
                network.peer.remote_print(src_conn, msg)
            if tgt_conn is not None and tgt_conn is not src_conn:
                network.peer.remote_print(tgt_conn, msg)
            return False
        # Check whether thit goes through
        if random.random() < sigmoid((src.dex - tgt.ref) / 10):
            msg = f"{src.cname} attempts to hit {tgt.cname}, but misses!"
            if src_conn is not None:
                network.peer.remote_print(src_conn, msg)
            return False
        # If hit goes through, get damage and modify health
        dmg = get_damage(src, tgt, wpn, slot)
        tgt.reduce_health(dmg)
        msg = f"{src.cname} hits {tgt.cname} for {dmg} damage!"
        if src_conn is not None:
            network.peer.remote_print(src_conn, msg)
        if tgt_conn is not None and tgt_conn is not src_conn:
            network.peer.remote_print(tgt_conn, msg)
        # Potentially raise skill level
        level_up, skill = get_level_up(src, tgt, wpn)
        if level_up:
            src.skills[skill_to_idx[skill]] += 1
            network.peer.remote_update_skills(src_conn, src.skills)
        return True

    def use_power(self, power):
        tgt = power.get_target(self.character)
        if tgt is None:
            return
        if self.character.energy < power.cost:
            return
        power.use(self.character, tgt)
        # Upon using a power, need to update energy to clients
        network.broadcast_cbstate_update(self.character)

    def handle_effects(self):
        """Increments effect timers and handles all necessary changes to character."""
        char = self.character
        updated_cbstate = False
        for effect in char.effects:
            effect_msgs = []
            remove = False
            if effect.timer == 0:
                effect_msgs += effect.apply_start_effects()
                effect.apply_persistent_effects()
                updated_cbstate = True
            if not char.alive:
                remove = True
            if effect.timer >= effect.duration:
                effect.remove_persistent_effects()
                effect_msgs += effect.apply_end_effects()
                remove = True
                updated_cbstate = True
            effect.tick_timer += time.dt
            if effect.tick_rate and effect.tick_timer >= effect.tick_rate:
                effect.tick_timer -= effect.tick_rate
                effect_msgs += effect.apply_tick_effects()
                updated_cbstate = True
            effect.timer += time.dt
            conn = network.uuid_to_connection.get(effect.src.uuid)
            if conn:
                for msg in effect_msgs:
                    network.peer.remote_print(conn, msg)
            if remove: 
                effect.remove()
        if updated_cbstate:
            network.broadcast_cbstate_update(char)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        # Assumed that keyboard component gets set by a client
        set_gravity_vel(self.character)
        set_jump_vel(self.character)
        displacement = get_displacement(self.character)
        self.character.position += displacement
        self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        # This executes client-side movement/rotation correct, to test movement without this
        # overhead, comment the rest of this function.
        for conn, uuid in network.connection_to_uuid.items():
            if self.character.uuid == uuid:
                network.peer.update_pc_lerp_attrs(conn, self.sequence_number, self.character.position,
                                                     self.character.rotation_y)
            else:
                network.peer.update_npc_lerp_attrs(conn, self.character.uuid, self.character.position,
                                                      self.character.rotation_y)

    def handle_movement_inputs(self, sequence_number, kb_direction, kb_y_rotation, mouse_y_rotation):
        """Processes movement inputs from a client"""
        char = self.character
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
        if sequence_number > self.sequence_number:
            self.sequence_number = sequence_number
        # Update client's NPC animation
        if kb_direction != Vec2(0, 0) and self.moving == False:
            self.moving = True
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_start_run_anim(conn, char.uuid)
        elif kb_direction == Vec2(0, 0) and self.moving == True:
            self.moving = False
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_end_run_anim(conn, char.uuid)

    def kill(self):
        self.character.alive = False
        uuid = self.character.uuid
        destroy(self.character)
        destroy(self)
        network.broadcast(network.peer.remote_kill, uuid)