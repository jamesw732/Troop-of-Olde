from ursina import *
import os
import json

from .effect import Effect

power_path = os.path.join(os.path.dirname(__file__), "..", "data", "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power(Entity):
    def __init__(self, power_id, char):
        super().__init__()
        power_id = str(power_id)
        power_data = id_to_power_data[power_id]
        for k, v in power_data.items():
            setattr(self, k, v)

        self.char = char

        # set to True immediately after use
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = 0

    def apply_effect(self):
        if self.target == "single":
            if not self.char.target or not self.char.target.alive:
                return ""
            effect = Effect(self.effect_id)
            return effect.apply_to_char(self.char.target)

