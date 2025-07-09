from ursina import *
import os
import json

from .base import data_path

power_path = os.path.join(data_path, "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power(Entity):
    """Base class for Powers which is the intersection of Client/Server Powers

    Powers are permanent objects which are bound to a database id.
    Spawn Effects when used server-side (and eventually client side).
    """
    def __init__(self, power_id, inst_id, on_use=lambda: None):
        """
        power_id: id that refers to a row in the database, note unique WRT instances
        inst_id: unique instance id used to refer to this power over the network"""
        super().__init__()
        self.power_id = power_id
        self.inst_id = inst_id
        self.on_use = on_use
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

    def use(self, src, tgt):
        self.start_cooldowns(src)
        self.on_use()

    def start_cooldowns(self, src):
        self.timer = 0
        self.on_cooldown = True
        src.energy -= self.cost
        src.gcd = self.gcd_duration
        src.gcd_timer = 0
        src.next_power = None

    def get_target(self, src):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return src.target

    def queue(self, src):
        src.next_power = self
