"""Defines states and declares a global game state. Most files will import this."""
from ursina import *
import math


class GameState:
    def __init__(self):
        self.pc = None # Player Controller
        self.world = None
        self.chars = [] # Characters

    def clear(self):
        """Called upon disconnect"""
        self.pc = None
        self.world = None
        self.chars.clear()

gs = GameState()


# Update this to expand PhysicalState
phys_state_attrs = {
    "model": str,
    "scale": Vec3,
    "position": Vec3,
    "rotation": Vec3,
    "color": str,

    "cname": str,
    "type": str,
    "target": int,
    "in_combat": bool,
}

class PhysicalState:
    """The real intention behind this class is to encompass client-authoritative
    Character attributes. Inclusions are pretty loose; for example in_combat seems
    like it should belong in CombatState but it makes more sense for it to be
    client-authoritative."""
    def __init__(self, char=None, **kwargs):
        """Possible kwargs given by phys_state_attrs.

        Explanations of nontrivial kwargs:
        color: string representing the color, ie "red" or "orange". See ursina.color.colors for possible keys
        target: uuid of character's target"""
        # If a character was passed, take its attributes
        if char is not None:
            for attr in phys_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        if attr in ["collider", "color", "model"]:
                            # Ursina objects exist in PhysicalState as string names
                            val = val.name
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in kwargs:
                if attr in phys_state_attrs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in phys_state_attrs if hasattr(self, attr)})


# Update this to expand CombatState
# Commented means not yet implemented
combat_state_attrs = {
    "health": int,
    # "mana": int,
    # "stamina": int,

    "bdy": int,
    "str": int,
    "dex": int,
    "ref": int,
    "agi": int,
    # "int": int,

    # "haste": int,
    "speed": int,
    # "armor": int,

    # "spellshield": int,
    # "rmagic": int,
    # "rphys": int,
    # "rfire": int,
    # "rcold": int,
    # "relec": int,
}

class CombatState:
    """The real intention behind this class is to encompass host-authoritative
    Character attributes. Pure combat vars like health and mana belong here, things
    like character target might not.

    The main implication of making this host-authoritative is that everything which
    affects combat state must be sent through the main client (host or offline client)
    to compute a new combat state. """
    def __init__(self, char=None, **kwargs):
        """Possible kwargs given by combat_state_attrs."""
        # If a character was passed, take its attributes
        if char is not None:
            for attr in combat_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in kwargs:
                if attr in combat_state_attrs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in combat_state_attrs if hasattr(self, attr)})


def sigmoid(x):
    return 1 / (1 + math.exp(-x))