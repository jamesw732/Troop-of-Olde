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
    def __init__(self, chars):
        super().__init__()
        self.chars = chars

    @every(dt)
    def tick_effects(self):
        """Increments effect timers and applies changes to character as needed"""
        for char in self.chars:
            updated_stats = False
            for effect in char.effects:
                effect_msgs = []
                remove = False
                if effect.timer == 0:
                    effect_msgs += effect.apply_start_effects()
                    effect.apply_persistent_effects()
                    updated_stats = True
                if not char.alive:
                    remove = True
                if effect.timer >= effect.duration:
                    effect.remove_persistent_effects()
                    effect_msgs += effect.apply_end_effects()
                    remove = True
                    updated_stats = True
                effect.tick_timer += dt
                if effect.tick_rate and effect.tick_timer >= effect.tick_rate:
                    effect.tick_timer -= effect.tick_rate
                    effect_msgs += effect.apply_tick_effects()
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
