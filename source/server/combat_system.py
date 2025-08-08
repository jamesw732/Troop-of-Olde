from ursina import *

from ..base import *
from ..combat import *
from ..network import network


dt = 1/5


class CombatSystem(Entity):
    """Ticks combat for all Characters.

    Increments combat timers for all characters that are in combat.
    If timer progresses past weapon's delay, performs an attack.
    """
    def __init__(self, chars):
        super().__init__()
        self.chars = chars

    @every(dt)
    def tick_combat(self):
        for char in self.chars:
            if not char.target or not char.target.alive:
                char.target = None
                char.mh_combat_timer = 0
                char.oh_combat_timer = 0
            elif char.in_combat:
                hit_mh = self.handle_combat(char, "mh")
                # See if we should progress offhand timer too
                # (if has skill dw):
                mh = char.equipment[slot_to_ind["mh"]]
                mh_is_1h = mh is None or mh.info.get("style", "")[:2] != "2h"
                hit_oh = False
                if mh_is_1h:
                    hit_oh = self.handle_combat(char, "oh")
                if hit_mh or hit_mh:
                    network.broadcast_cbstate_update(char.target)

    def handle_combat(self, src, slot):
        tgt = src.target
        src_conn = network.uuid_to_connection.get(src.uuid, None)
        tgt_conn = network.uuid_to_connection.get(tgt.uuid, None)
        idx = slot_to_ind[slot]
        wpn = src.equipment[idx]
        # Check whether to attempt to perform an attack or not
        attempting = tick_combat_timer(src, slot, wpn, dt)
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

