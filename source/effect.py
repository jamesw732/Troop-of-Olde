from ursina import *
import os
import json
import copy

from .gamestate import gs


effects_path = os.path.join(os.path.dirname(__file__), "..", "data", "effects.json")
with open(effects_path) as effects_json:
    id_to_effect_data = json.load(effects_json)


class Effect(Entity):
    """Represents the actual effect of things like powers and procs.

    Current implementation is very simplistic and needs expanding.
    Effects are temporary objects by definition."""
    def __init__(self, effect_id, src, tgt):
        super().__init__()
        effect_id = str(effect_id)
        effect_data = copy.deepcopy(id_to_effect_data[effect_id])
        self.effect_type = effect_data["effect_type"]
        self.effects = effect_data["effects"]
        self.src = src
        self.tgt = tgt
        self.hit = False

        if self.effect_type == "persistent":
            self.timer = 0

    def attempt_apply(self):
        """Main driving method called by the server for applying an effect to a target"""
        assert gs.network.peer.is_hosting()
        if self.tgt is None:
            return
        self.check_land()
        if self.hit:
            self.apply_mods()
            self.apply()
            gs.network.broadcast_cbstate_update(self.src)
            if self.src != self.tgt:
                gs.network.broadcast_cbstate_update(self.tgt)
        msg = self.get_msg()
        gs.network.broadcast(gs.network.peer.remote_print, msg)

    def check_land(self):
        """Performs a random roll to determine whether the effect is applied or not"""
        # Currently bare, will eventually need a formula
        self.hit = True

    def apply_mods(self):
        if not self.hit:
            return
        if self.effect_type == "instant":
            if "damage" in self.effects:
                self.effects["damage"] -= self.tgt.armor

    def get_msg(self):
        if not self.hit:
            return f"{self.src.cname} misses {self.tgt.cname}."
        msg = ""
        if self.effect_type == "instant":
            if "damage" in self.effects:
                dmg = self.effects["damage"]
                msg = f"{self.tgt.cname} is damaged for {dmg} damage!"
            if "heal" in self.effects:
                heal = self.effects["heal"]
                msg = f"{self.src.cname} heals {self.tgt.cname} for {heal} health!"
        return msg

    def apply(self):
        if not self.hit:
            return
        if self.effect_type == "instant":
            self.apply_instant()

    def apply_instant(self):
        if not self.hit or self.effect_type != "instant":
            return
        if "damage" in self.effects:
            dmg = self.effects["damage"]
            self.tgt.reduce_health(dmg)
        if "heal" in self.effects:
            heal = self.effects["heal"]
            self.tgt.increase_health(heal)
