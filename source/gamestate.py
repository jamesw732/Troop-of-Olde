"""Defines states and declares a global game state. Most files will import this."""


class GameState:
    def __init__(self):
        self.pc = None # Player Character
        self.playercontroller = None
        self.world = None
        self.chars = [] # Characters
        self.network = None
        self.ui = None

    def clear(self):
        """Called upon disconnect"""
        self.pc = None
        self.playercontroller = None
        self.world = None
        self.chars.clear()
        self.network = None
        self.ui = None

gs = GameState()