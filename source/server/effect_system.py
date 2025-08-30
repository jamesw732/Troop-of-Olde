from ursina import *

from .effect import *
from ..base import *
from ..network import network


dt = 1/5


class EffectSystem(Entity):
    """Handles effect processing for all Characters.

    Increments timers for all effects across all characters.
    Applies start effects, tick effects, and end effects.
    """
    def __init__(self, gamestate, stat_manager):
        super().__init__()
        self.chars = gamestate.uuid_to_char.values()
        self.effect_inst_id_counter = 0
        self.inst_id_to_effect = gamestate.inst_id_to_effect
        self.stat_manager = stat_manager

    def make_effect(self, effect_mnem, src, tgt):
        effect = Effect(effect_mnem, src, tgt)
        self.inst_id_to_effect[self.effect_inst_id_counter] = effect
        self.effect_inst_id_counter += 1
        return Effect(effect_mnem, src, tgt)

    @every(dt)
    def tick_effects(self):
        """Increments effect timers and applies changes to character as needed"""
        for char in self.chars:
            updated_stats = False
            for effect in char.effects:
                effect_msgs = []
                remove = False
                if effect.timer == 0:
                    effect_msgs += self.apply_instant_effects(effect, effect_key="start")
                    self.apply_persistent_effects(effect)
                    updated_stats = True
                if not char.alive:
                    remove = True
                if effect.timer >= effect.duration:
                    self.remove_persistent_effects(effect)
                    effect_msgs += self.apply_instant_effects(effect, effect_key="end")
                    remove = True
                    updated_stats = True
                effect.tick_timer += dt
                if effect.tick_rate and effect.tick_timer >= effect.tick_rate:
                    effect.tick_timer -= effect.tick_rate
                    effect_msgs += self.apply_instant_effects(effect, effect_key="tick")
                    updated_stats = True
                effect.timer += dt
                conn = network.uuid_to_connection.get(effect.src.uuid)
                if conn:
                    for msg in effect_msgs:
                        network.peer.remote_print(conn, msg)
                if remove: 
                    effect.remove()
            if updated_stats:
                network.broadcast_cbstate_update(char)

    def apply_persistent_effects(self, effect):
        """Applies stat changes caused by a persistent effect.
        These are lasting, they affect the character until this effect is removed."""
        self.stat_manager.apply_state_diff(effect.tgt, effect.persistent_state)

    def remove_persistent_effects(self, effect):
        """Removes stat changes caused by a persistent effect."""
        self.stat_manager.apply_state_diff(effect.tgt, effect.persistent_state, remove=True)

    def apply_instant_effects(self, effect, effect_key="start"):
        """Apply one of effect.start_effects, tick_effects, end_effects to effect.tgt

        effect_key is one of "start", "tick", "end"
        """
        key_to_effects = {
            "start": effect.start_effects,
            "tick": effect.tick_effects,
            "end": effect.end_effects
        }
        effects = key_to_effects.get(effect_key, {})
        msgs = []
        for name, val in effects.items():
            # Get modified value based on src and tgt stats
            # Consider pulling out into separate function
            if name == "damage":
                val -= effect.tgt.armor
            self.apply_instant_statchange(effect.tgt, name, val)
            msgs.append(effect.get_msg(name, val))
        return msgs

    def apply_instant_statchange(self, tgt, name, val):
        """Helper function for applying a single stat change"""
        if name == "damage":
            self.stat_manager.reduce_health(tgt, val)
        elif name == "heal":
            self.stat_manager.increase_health(tgt, val)
