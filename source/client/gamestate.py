class GameState:
    """Stores bottom-level containers for all Systems and Managers to access and update

    Objects may be added to these by any System or Manager, but only CleanupManager
    should remove objects from them."""
    def __init__(self):
        self.pc = None
        self.pc_ctrl = None
        self.cam_ctrl = None
        self.uuid_to_char = dict()
        self.uuid_to_ctrl = dict()
        self.uuid_to_labl = dict()
        self.uuid_to_anim = dict()
        self.uuid_to_lerp = dict()
        self.inst_id_to_item = dict()
        self.inst_id_to_power = dict()
        self.cooldown_powers = dict()
