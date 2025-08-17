from ursina import *


class CleanupManager(Entity):
    """Provides an interface for cleaning up all game objects.

    If this class becomes cluttered, do not hesitate to split this up
    by object."""
    def __init__(self, gamestate):
        super().__init__()
        self.gamestate = gamestate

    def cleanup_pc(self):
        pc = self.gamestate.pc
        self.gamestate.pc = None
        del self.gamestate.uuid_to_char[uuid]
        pc.model_child.detachNode()
        del pc.model_child
        for src in pc.targeted_by:
            src.target = None
        pc.targeted_by = []
        pc.ignore_traverse = []
        pc.alive = False
        destroy(pc)
        # Clean up Controller... maybe separate this out into a separate method
        pc_ctrl = self.gamestate.pc_ctrl
        self.gamestate.pc_ctrl = None
        del self.gamestate.uuid_to_ctrl[uuid]
        del pc_ctrl.animator
        destroy(pc_ctrl.focus)
        del pc_ctrl.focus
        destroy(pc_ctrl)
        # Clean up NameLabel
        namelabel = self.gamestate.uuid_to_labl[uuid]
        del namelabel.char
        del self.gamestate.uuid_to_labl[uuid]
        destroy(namelabel)
        # Clean up the animator
        animator = self.gamestate.uuid_to_anim[uuid]
        del animator.actor
        del self.gamestate.uuid_to_anim[uuid]

    def cleanup_npc(self, uuid):
        char = self.gamestate.uuid_to_char[uuid]
        del self.gamestate.uuid_to_char[uuid]
        char.model_child.detachNode()
        del char.model_child
        for src in char.targeted_by:
            src.target = None
        char.targeted_by = []
        char.ignore_traverse = []
        char.alive = False
        destroy(char)
        # Clean up Controller... maybe separate this out into a separate method
        ctrl = self.gamestate.uuid_to_ctrl[uuid]
        del self.gamestate.uuid_to_ctrl[uuid]
        del ctrl.animator
        destroy(ctrl)
        # Clean up NameLabel
        namelabel = self.gamestate.uuid_to_labl[uuid]
        del namelabel.char
        del self.gamestate.uuid_to_labl[uuid]
        destroy(namelabel)
        # Clean up the animator
        animator = self.gamestate.uuid_to_anim[uuid]
        del animator.actor
        del self.gamestate.uuid_to_anim[uuid]


