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
        elif char.next_power is not None and not char.next_power.on_cooldown:
            self.use_power(char.next_power)
        self.handle_effects()

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
            src.skills[skill] += 1
        return True

    def use_power(self, power):
        tgt = power.get_target(self.character)
        if tgt is None:
            return
        if self.character.energy < power.cost:
            return
        power.use(self.character, tgt)

    def handle_effects(self):
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
        if displacement == Vec3(0, 0, 0):
            return
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

    def kill(self):
        self.character.alive = False
        uuid = self.character.uuid
        destroy(self.character)
        destroy(self)
        network.broadcast(network.peer.remote_kill, uuid)