from ursina import *
import os
import json

from .gamestate import gs


effects_path = os.path.join(os.path.dirname(__file__), "..", "data", "effects.json")
with open(effects_path) as effects_json:
    id_to_effect_data = json.load(effects_json)


class Effect(Entity):
    def __init__(self, effect_id):
        super().__init__()
        effect_id = str(effect_id)
        effect_data = id_to_effect_data[effect_id]
        for k, v in effect_data.items():
            setattr(self, k, v)

        if self.effect_type == "persistent":
            self.timer = 0

    def apply_to_char(self, src, tgt):
        msg = ""
        if self.effect_type == "instant":
            if "damage" in self.effects:
                dmg = self.effects["damage"]
                tgt.health -= dmg
                gs.network.broadcast_cbstate_update(tgt)
                msg = f"{tgt.cname} is damaged for {dmg} damage!"
            destroy(self)
        return msg

        
