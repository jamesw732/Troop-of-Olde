"""Defines states and declares a global game state. Most files will import this."""


class GameState:
    def __init__(self):
        self.input_handler = None
        self.pc = None # Player Character
        self.playercontroller = None
        self.world = None
        self.chars = [] # Characters
        self.ui = None

    def clear(self):
        """Called upon disconnect"""
        self.input_handler = None
        self.pc = None
        self.playercontroller = None
        self.world = None
        self.chars.clear()
        self.ui = None

gs = GameState()