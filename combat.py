"""Contains combat computations mutual to all mobs. All calculations performed at the level of mob."""

from ursina import *
from mob import Mob

class Combat:
    def __init__(self, moblist):
        """moblist: list of all mobs in current scene, will be updated externally"""
        self.moblist = moblist

    def damage(self, src, tgt, damage):
        """
        src: mob
        tgt: mob
        damage: int"""
        print(f"{src.character.name} pummels {tgt.character.name} for {damage} damage!")
        tgt.health -= damage
        if tgt.health <= 0:
            tgt.die()
            src.target = None
    
    def attempt_hit(self, src, tgt, damage=10):
        """
        src: mob
        tgt: mob
        damage: int"""
        self.damage(src, tgt, damage)
    
    def get_tgt_hittable(self, src, tgt):
        dist = distance(src.character, src.target.character)
        if dist < src.attackrange:
            src_pos = src.character.position + Vec3(0, 0.8 * src.character.scale_y, 0)
            tgt_pos = tgt.character.position + Vec3(0, 0.8 * tgt.character.scale_y, 0)
            dir = tgt_pos - src_pos
            line_of_sight = raycast(src_pos, direction=dir, distance=dist, ignore=[mob.character for mob in self.moblist])
            if len(line_of_sight.entities) == 0:
                return True
            else:
                print(f"{tgt.character.name} is out of sight.")
        else:
            print(f"{tgt.character.name} is too far away.")
        return False

    def main_combat_loop(self):
        for mob in self.moblist:
            if mob.combat and mob.target:
                mob.combat_timer += time.dt
                if mob.combat_timer > mob.max_combat_timer:
                    mob.combat_timer -= mob.max_combat_timer
                    if self.get_tgt_hittable(mob, mob.target):
                        self.attempt_hit(mob, mob.target)