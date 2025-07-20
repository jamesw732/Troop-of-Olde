from ursina import *
import numpy as np
import quaternion


idle_anim = "Idle"
run_anim = "RunCycle"


class Anim(Entity):
    """Wrapper for Actor animation methods that encapsulates common animation sequences"""
    def __init__(self, actor):
        """actor: a Panda3D Actor object, which is the target of animation."""
        super().__init__()
        self.actor = actor
        self.actor.loop(idle_anim)
        self.cur_anim = idle_anim
        self.idle_anim = idle_anim
        self.actor.enableBlend()
        self.anim_blends = dict()
        self.fade_in_anims = dict()
        self.fade_out_anims = dict()

    def update(self):
        # Convert to list because we might be removing from dict
        for name, t in list(self.fade_in_anims.items()):
            w = self.get_anim_blend(name) + time.dt / t
            w = min(w, 1)
            self.set_anim_blend(name, w)
            if w == 1:
                del self.fade_in_anims[name]
        for name, t in list(self.fade_out_anims.items()):
            w = self.get_anim_blend(name) - time.dt / t
            w = max(w, 0)
            self.set_anim_blend(name, w)
            if w == 0:
                del self.fade_out_anims[name]

    def start_run_cycle(self):
        """Starts run cycle"""
        # if self.actor.getCurrentAnim() is None:
        if self.cur_anim == run_anim:
            return
        self.actor.loop(run_anim)
        self.fade_in_anim(run_anim, 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = run_anim

    def start_idle(self):
        """Starts idle animation, which is either the Idle animation or CombatStance."""
        if self.cur_anim == self.idle_anim:
            return
        self.actor.loop(self.idle_anim)
        self.fade_in_anim(self.idle_anim, 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = self.idle_anim

    def enter_combat(self):
        self.idle_anim = "CombatStance"
        if self.cur_anim == idle_anim:
            self.start_idle()

    def exit_combat(self):
        self.idle_anim = idle_anim
        if self.cur_anim == "CombatStance":
            self.start_idle()

    def do_attack(self, slot):
        if slot == "mh":
            anim = "PunchRight"
        elif slot == "oh":
            anim = "PunchLeft"
        self.actor.play(anim)
        # time = num frames / 24 fps
        t = self.actor.get_anim_control(anim).get_num_frames() / 24
        def start():
            self.fade_in_anim(anim, 0.2)
            self.fade_out_anim(self.cur_anim, 0.2)
        def end():
            self.fade_in_anim(self.cur_anim, 0.2)
            self.fade_out_anim(anim, 0.2)
        s = Sequence(start, Wait(t), end)
        # Forcing sequence to go to end means that the player holds combat
        # stance for too long. Not an urgent issue to fix, but should probably
        # be handled better in the future.
        s.start()

    def fade_in_anim(self, name, t):
        if name in self.fade_out_anims:
            del self.fade_out_anims[name]
        self.fade_in_anims[name] = t

    def fade_out_anim(self, name, t):
        if name in self.fade_in_anims:
            del self.fade_in_anims[name]
        self.fade_out_anims[name] = t

    def get_anim_blend(self, name):
        return self.anim_blends.get(name, 0)

    def set_anim_blend(self, name, w):
        self.anim_blends[name] = w
        self.actor.setControlEffect(name, w)
