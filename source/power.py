from ursina import *
import os
import json

from .base import data_path
from .network import network

power_path = os.path.join(data_path, "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power(Entity):
    """Base class for Powers which is the intersection of Client/Server Powers

    Powers are permanent objects which are bound to a character and database id.
    Dual relationship with Effects, which are temporary objects spawned when a Power is used.
    """
    def __init__(self, char, power_id, inst_id):
        """
        char: Character that has access to this Power
        power_id: id that refers to a row in the database, note unique WRT instances
        inst_id: unique instance id used to refer to this power over the network"""
        super().__init__()
        self.char = char
        self.power_id = power_id
        self.inst_id = inst_id
        network.inst_id_to_power[self.inst_id] = self
        power_data = id_to_power_data[str(power_id)]
        # Would it be better to be more explicit about this?
        for k, v in power_data.items():
            setattr(self, k, v)
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = self.cooldown

    def update(self):
        """Handle individual cooldown logic"""
        # Note GCD logic is handled by char.tick_gcd and MobController.update
        if self.on_cooldown:
            self.timer += time.dt
            if self.timer >= self.cooldown:
                self.on_cooldown = False

    def use(self):
        self.char.energy -= self.cost
        self.char.gcd = self.gcd_duration
        self.char.gcd_timer = 0
        self.timer = 0
        self.char.next_power = None
        self.on_cooldown = True

    def get_target(self):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return self.char.target

    def queue(self):
        self.char.next_power = self
