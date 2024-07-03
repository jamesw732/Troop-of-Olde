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

def sigmoid(x):
    return 1 / (1 + math.exp(-x))