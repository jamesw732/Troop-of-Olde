from ursina import *
import os
import json
import copy

from .. import data_path, Stats


effects_path = os.path.join(data_path, "effects.json")
with open(effects_path) as effects_json:
    mnem_to_effect_data = json.load(effects_json)


class Effect:
    """Represents the actual effect of things like powers and procs.

    Effects are temporary objects which are the result of powers etc.
    This class does not actually drive the Effect logic, instead it
    provides an API for creating effects and attaching them to
    characters. The driving logic is delegated to MobController.
    """
    def __init__(self, effect_mnem, src, tgt):
        self.effect_mnem = effect_mnem
        effect_data = copy.deepcopy(mnem_to_effect_data[effect_mnem])
        self.start_effects = effect_data.get("start_effects", {})
        self.tick_effects = effect_data.get("tick_effects", {})
        self.persistent_effects = effect_data.get("persistent_effects", {})
        self.persistent_state = Stats(self.persistent_effects)
        self.end_effects = effect_data.get("end_effects", {})
        self.duration = effect_data.get("duration", 0)
        self.tick_rate = effect_data.get("tick_rate", 0)
        self.timer = 0
        self.tick_timer = 0
        self.src = src
        self.tgt = tgt

    def attempt_apply(self):
        """Main driving method called by the server for applying an effect to a target"""
        if self.src is None or self.tgt is None:
            return
        if self.check_land():
            self.apply()
            return True
        return False

    def check_land(self):
        """Performs a random roll to determine whether the effect is applied or not"""
        # Currently bare, will eventually need a formula
        return True

    def apply(self):
        """Adds this effect to the target, removing duplicates beforehand"""
        dupes = [eff for eff in self.tgt.effects if eff == self]
        if len(dupes) > 0:
            for dupe in dupes:
                dupe.remove()
        self.tgt.effects.append(self)

    def remove(self):
        """Removes this effect from the target. Does not apply end effects"""
        self.tgt.effects.remove(self)
        del self.src
        del self.tgt

    def apply_persistent_effects(self):
        """Applies stat changes caused by a persistent effect.
        These are lasting, they affect the character until this effect is removed."""
        self.persistent_state.apply_diff(self.tgt)
        self.tgt.update_max_ratings()

    def remove_persistent_effects(self):
        """Removes stat changes caused by a persistent effect."""
        self.persistent_state.apply_diff(self.tgt, remove=True)
        self.tgt.update_max_ratings()

    def apply_start_effects(self):
        """Applies stat changes caused by the start of the effect.
        Returns messages resulting from  these effects."""
        return self.apply_instant_effects(self.start_effects)

    def apply_tick_effects(self):
        """Applies stat changes caused by effects that tick over time.
        Returns messages resulting from  these effects."""
        return self.apply_instant_effects(self.tick_effects)

    def apply_end_effects(self):
        """Applies stat changes caused by the end of the effect.
        Returns messages resulting from these effects."""
        return self.apply_instant_effects(self.end_effects)

    def apply_instant_effects(self, effects):
        """Apply instant type effects.
        effects: one of self.start_effects, self.tick_effects, self.end_effects
        """
        msgs = []
        for name, val in effects.items():
            val = self.get_modified_val(name, val)
            self.apply_subeffect(name, val)
            msgs.append(self.get_msg(name, val))
        self.tgt.update_max_ratings()
        return msgs

    def get_modified_val(self, name, val):
        """Modify value based on self.src/self.tgt"""
        if name == "damage":
            val -= self.tgt.armor
        return val

    def apply_subeffect(self, name, val):
        """Helper function for applying all types of effects"""
        if name == "damage":
            self.tgt.reduce_health(val)
        elif name == "heal":
            self.tgt.increase_health(val)

    def get_msg(self, name, val):
        msg = ""
        if name == "damage":
            msg = f"{self.tgt.cname} is damaged for {val} damage!"
        if name == "heal":
            msg = f"{self.src.cname} heals {self.tgt.cname} for {val} health!"
        return msg

    def __eq__(self, other):
        return self.src.uuid == other.src.uuid and self.tgt.uuid == other.tgt.uuid \
                and self.effect_mnem == other.effect_mnem
