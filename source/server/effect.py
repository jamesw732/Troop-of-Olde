from ursina import *
import os
import json
import copy

from .. import data_path, network, Stats


effects_path = os.path.join(data_path, "effects.json")
with open(effects_path) as effects_json:
    id_to_effect_data = json.load(effects_json)


class Effect(Entity):
    """Represents the actual effect of things like powers and procs.

    Should only be instantiated server-side. Effects are temporary objects
    which last for a fixed rotation or for only an instant."""
    def __init__(self, effect_id, src, tgt):
        super().__init__()
        effect_id = str(effect_id)
        effect_data = copy.deepcopy(id_to_effect_data[effect_id])
        self.instant_effects = effect_data.get("instant_effects", {})
        self.tick_effects = effect_data.get("tick_effects", {})
        self.persistent_effects = effect_data.get("persistent_effects", {})
        self.persistent_state = Stats(self.persistent_effects)
        self.duration = effect_data.get("duration", 0)
        self.tick_rate = effect_data.get("tick_rate", 0)
        self.timer = 0
        self.tick_timer = 0
        self.src = src
        self.tgt = tgt
        self.hit = False

    def update(self):
        """Update tick effects and overall timer, destroy if past duration"""
        if not self.tgt.alive or self.timer >= self.duration:
            self.persistent_state.apply_diff(self.tgt, remove=True)
            self.tgt.update_max_ratings()
            network.broadcast_cbstate_update(self.tgt)
            destroy(self)
        self.tick_timer += time.dt
        if self.tick_rate and self.tick_timer >= self.tick_rate:
            self.tick_timer -= self.tick_rate
            for name, val in self.tick_effects.items():
                val = self.get_modified_val(name, val)
                self.apply_subeffect(name, val)
            network.broadcast_cbstate_update(self.tgt)
        self.timer += time.dt

    def attempt_apply(self):
        """Main driving method called by the server for applying an effect to a target"""
        assert network.peer.is_hosting()
        if self.tgt is None:
            return
        self.check_land()
        if self.hit:
            self.apply()
            network.broadcast_cbstate_update(self.src)
            if self.src != self.tgt:
                network.broadcast_cbstate_update(self.tgt)

    def check_land(self):
        """Performs a random roll to determine whether the effect is applied or not"""
        # Currently bare, will eventually need a formula
        self.hit = True

    def apply(self):
        """Handle instant effects and begin persistent effects"""
        if not self.hit:
            msg = f"{self.src.cname} misses {self.tgt.cname}."
            network.broadcast(network.peer.remote_print, msg)
            return
        for name, val in self.instant_effects.items():
            val = self.get_modified_val(name, val)
            self.apply_subeffect(name, val)
        self.persistent_state.apply_diff(self.tgt)
        self.tgt.update_max_ratings()

    def apply_subeffect(self, name, val):
        """Helper function for applying all types of effects"""
        if name == "damage":
            self.tgt.reduce_health(val)
        elif name == "heal":
            self.tgt.increase_health(val)
        msg = self.get_msg(name, val)
        network.broadcast(network.peer.remote_print, msg)

    def get_modified_val(self, name, val):
        """Modify value based on self.src/self.tgt"""
        if name == "damage":
            val -= self.tgt.armor
        return val

    def get_msg(self, name, val):
        msg = ""
        if name == "damage":
            msg = f"{self.tgt.cname} is damaged for {val} damage!"
        if name == "heal":
            msg = f"{self.src.cname} heals {self.tgt.cname} for {val} health!"
        return msg
