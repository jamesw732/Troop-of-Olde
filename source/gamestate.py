"""Declares game state, relevant to both online and single player"""

class GameState:
    def __init__(self):
        self.pc = None # Player Controller
        self.world = None
        self.chars = [] # Characters

    def clear(self):
        self.pc = None
        self.world = None
        self.chars.clear()

gs = GameState()