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
        self.instant_effects = effect_data.get("instant_effects", {})
        self.tick_effects = effect_data.get("tick_effects", {})
        self.persistent_effects = effect_data.get("persistent_effects", {})
        self.duration = effect_data.get("duration", 0)
        self.timer = 0
        self.tick_timers = {name: 0 for name in self.tick_effects}
        self.src = src
        self.tgt = tgt
        self.hit = False

    def update(self):
        """Update tick effects and overall timer, destroy if past duration"""
        if not self.tgt.alive or self.timer >= self.duration:
            destroy(self)
        for name in self.tick_timers:
            self.tick_timers[name] += time.dt
            if self.tick_timers[name] >= self.tick_effects[name][1]:
                self.tick_timers[name] -= self.tick_effects[name][1]
                val = self.get_modified_val(name, self.tick_effects[name][0])
                self.apply_subeffect(name, val)
        self.timer += time.dt

    def attempt_apply(self):
        """Main driving method called by the server for applying an effect to a target"""
        assert gs.network.peer.is_hosting()
        if self.tgt is None:
            return
        self.check_land()
        if self.hit:
            self.apply()
            gs.network.broadcast_cbstate_update(self.src)
            if self.src != self.tgt:
                gs.network.broadcast_cbstate_update(self.tgt)

    def check_land(self):
        """Performs a random roll to determine whether the effect is applied or not"""
        # Currently bare, will eventually need a formula
        self.hit = True

    def apply(self):
        """Handle instant effects and begin persistent effects"""
        if not self.hit:
            msg = f"{self.src.cname} misses {self.tgt.cname}."
            gs.network.broadcast(gs.network.peer.remote_print, msg)
            return
        for name, val in self.instant_effects.items():
            val = self.get_modified_val(name, val)
            self.apply_subeffect(name, val)

    def apply_subeffect(self, name, val):
        """Helper function for applying all types of effects"""
        if name == "damage":
            self.tgt.reduce_health(val)
        elif name == "heal":
            self.tgt.increase_health(val)
        msg = self.get_msg(name, val)
        gs.network.broadcast(gs.network.peer.remote_print, msg)

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


# class Effect(Entity):
#     """Represents the actual effect of things like powers and procs.

#     Current implementation is very simplistic and needs expanding.
#     Effects are temporary objects by definition."""
#     def __init__(self, effect_data, src, tgt):
#         super().__init__()
#         self.effects = effect_data["effects"]
#         self.src = src
#         self.tgt = tgt
#         self.hit = False

#     def attempt_apply(self):
#         """Main driving method called by the server for applying an effect to a target"""
#         assert gs.network.peer.is_hosting()
#         if self.tgt is None:
#             return
#         self.check_land()
#         if self.hit:
#             self.apply_mods()
#             self.apply()
#             gs.network.broadcast_cbstate_update(self.src)
#             if self.src != self.tgt:
#                 gs.network.broadcast_cbstate_update(self.tgt)
#         msg = self.get_msg()
#         gs.network.broadcast(gs.network.peer.remote_print, msg)

#     def check_land(self):
#         """Performs a random roll to determine whether the effect is applied or not"""
#         # Currently bare, will eventually need a formula
#         self.hit = True


# class InstantEffect(Effect):
#     def __init__(self, effect_data, src, tgt):
#         super().__init__(effect_data, src, tgt)

#     def apply_mods(self):
#         if not self.hit:
#             return
#         if "damage" in self.effects:
#             self.effects["damage"] -= self.tgt.armor

#     def get_msg(self):
#         if not self.hit:
#             return f"{self.src.cname} misses {self.tgt.cname}."
#         msg = ""
#         if "damage" in self.effects:
#             dmg = self.effects["damage"]
#             msg = f"{self.tgt.cname} is damaged for {dmg} damage!"
#         if "heal" in self.effects:
#             heal = self.effects["heal"]
#             msg = f"{self.src.cname} heals {self.tgt.cname} for {heal} health!"
#         return msg

#     def apply(self):
#         if not self.hit:
#             return
#         if "damage" in self.effects:
#             dmg = self.effects["damage"]
#             self.tgt.reduce_health(dmg)
#         if "heal" in self.effects:
#             heal = self.effects["heal"]
#             self.tgt.increase_health(heal)

# class PersistentEffect(Effect):
#     def __init__(self, effect_data, src, tgt):
#         super().__init__(effect_data, src, tgt)
#         self.effects = effect_data.get("effects", {})
#         self.tick_effects = effect_data.get("tick_effects", {})
#         self.tick_timers = {name: effect[1] for name, effect in self.tick_effects.items()}
#         self.duration = effect_data["duration"]
#         self.timer = 0

#     def update(self):
#         for name in self.tick_timers:
#             self.tick_timers[name] += time.dt
#             if self.tick_timers[name] >= self.tick_effecs[name][1]:
#                 self.tick_timers[name] -= self.tick_effects[name][1]
#             # Perform the effect
                
#         self.timer += time.dt
#         if self.timer >= self.duration:
#             # remove stats and destroy self
#             destroy(self)
