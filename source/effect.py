from ursina import *
import os
import json
import copy

from .gamestate import gs


effects_path = os.path.join(os.path.dirname(__file__), "..", "data", "effects.json")
with open(effects_path) as effects_json:
    id_to_effect_data = json.load(effects_json)


class Effect(Entity):
    """Represents the actual effect of things like powers and procs

    Current implementation is very simplistic and needs expanding."""
    def __init__(self, effect_id):
        super().__init__()
        effect_id = str(effect_id)
        effect_data = copy.deepcopy(id_to_effect_data[effect_id])
        self.effect_type = effect_data["effect_type"]
        self.effects = effect_data["effects"]
        self.hit = False

        if self.effect_type == "persistent":
            self.timer = 0

    def attempt_apply(self, src, tgt):
        """Main driving method called by the server for applying an effect to a target"""
        assert gs.network.peer.is_hosting()
        hit = self.get_hit(src, tgt)
        if hit:
            self.apply_mods(src, tgt)
            self.apply(src, tgt)
        msg = self.get_msg(src, tgt)
        gs.network.broadcast_cbstate_update(src)
        gs.network.broadcast(gs.network.peer.remote_print, msg)

    def get_hit(self, src, tgt):
        self.hit = True
        return True

    def apply_mods(self, src, tgt):
        if not self.hit:
            return
        if self.effect_type == "instant":
            if "damage" in self.effects:
                self.effects["damage"] -= tgt.armor

    def get_msg(self, src, tgt):
        if not self.hit:
            return f"{src.cname} misses {tgt.cname}."
        if self.effect_type == "instant":
            if "damage" in self.effects:
                dmg = self.effects["damage"]
                msg = f"{tgt.cname} is damaged for {dmg} damage!"
        return msg

    def apply(self, src, tgt):
        if not self.hit:
            return
        if self.effect_type == "instant":
            if "damage" in self.effects:
                dmg = self.effects["damage"]
                tgt.health -= dmg
