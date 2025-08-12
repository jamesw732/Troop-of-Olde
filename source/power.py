from ursina import *
import os
import json

from .base import data_path

power_path = os.path.join(data_path, "powers.json")
with open(power_path) as power_json:
    mnem_to_power_data = json.load(power_json)


class Power:
    """Base class for Powers which is the intersection of Client/Server Powers

    Powers are permanent objects which are bound to a database id.
    Spawn Effects when used server-side (and eventually client side).
    """
    def __init__(self, power_mnem, inst_id):
        """
        power_id: id that refers to a row in the database, note unique WRT instances
        inst_id: unique instance id used to refer to this power over the network"""
        super().__init__()
        self.power_mnem = power_mnem
        self.inst_id = inst_id
        power_data = mnem_to_power_data[power_mnem]
        # Would it be better to be more explicit about this?
        for k, v in power_data.items():
            setattr(self, k, v)
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = self.cooldown

    def tick_cd(self, dt):
        if self.on_cooldown:
            self.timer = min(self.cooldown, self.timer + dt)
            if self.timer >= self.cooldown:
                self.on_cooldown = False

    def start_cooldown(self):
        self.timer = 0
        self.on_cooldown = True

    def get_target(self, src):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return src.target

    def queue(self, src):
        src.next_power = self
