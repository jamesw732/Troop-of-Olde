class GlobalContainers:
    """Stores global containers for all Systems and Managers to access and write to

    Objects may be added to these by any System or Manager, but only CleanupManager
    should remove objects from them."""
    def __init__(self):
        self.uuid_to_char = dict()
        self.uuid_to_ctrl = dict()
        self.inst_id_to_item = dict()
        self.inst_id_to_effect = dict()
        self.inst_id_to_power = dict()
        self.cooldown_powers = dict()
        self.gcd_chars = dict()
