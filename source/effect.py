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

    Current implementation is very simplistic and needs expanding.
    Basic usage flow of this class is as follows:
    Create an Effect whenever needed, ie when the player tries to use a Power
    Call get_hit to see whether the effect actually landed or not
    Call apply_mods to modify the effect based on source and target's stats. This modifies the actual effect_data
    Call apply_effect to actually apply the effect. Result will get sent back to client."""
    def __init__(self, effect_id):
        super().__init__()
        effect_id = str(effect_id)
        effect_data = copy.deepcopy(id_to_effect_data[effect_id])
        self.effect_type = effect_data["effect_type"]
        self.effects = effect_data["effects"]
        self.hit = False

        if self.effect_type == "persistent":
            self.timer = 0

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

    def apply_to_char(self, src, tgt):
        if not self.hit:
            return
        if self.effect_type == "instant":
            if "damage" in self.effects:
                dmg = self.effects["damage"]
                tgt.health -= dmg
