from .action_bar import ActionBar
from .bars import BarWindow
from .game_window import GameWindow
from .items_system import ItemsSystem
from .player_window import PlayerWindow


class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None
        self.actionbar = None
        self.items_system = None

    def make_all_ui(self, world):
        char = world.pc
        power_system = world.power_system

        self.items_system = ItemsSystem(char)
        self.bars = BarWindow(char)
        self.playerwindow = PlayerWindow(char, self.items_system)
        self.gamewindow = GameWindow()
        self.actionbar = ActionBar(char, power_system)


ui = UI()
