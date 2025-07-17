from ursina import *
import numpy as np
import quaternion

class Anim(Entity):
    """Wrapper for Actor animation methods that encapsulates common animation sequences"""
    def __init__(self, actor):
        """actor: a Panda3D Actor object, which is the target of animation."""
        super().__init__()
        self.actor = actor
        self.actor.loop("Idle")
        self.cur_anim = "Idle"
        self.idle_anim = "Idle"
        # This describes the current animation being looped
        self.state = "idle"
        # This describes the idle animation to loop, either idle or combat
        self.idle_state = "idle"
        self.actor.enableBlend()
        self.fade_in_anims = {}
        self.fade_out_anims = {}

    def update(self):
        for name, (t, w) in list(self.fade_in_anims.items()):
            w = min(w + time.dt / t, 1)
            self.actor.setControlEffect(name, w)
            if w == 1:
                del self.fade_in_anims[name]
            else:
                self.fade_in_anims[name] = (t, w)
        for name, (t, w) in list(self.fade_out_anims.items()):
            w = max(w - time.dt / t, 0)
            self.actor.setControlEffect(name, w)
            if w == 0:
                del self.fade_out_anims[name]
            else:
                self.fade_out_anims[name] = (t, w)

    def start_run_cycle(self):
        """Starts run cycle"""
        # if self.actor.getCurrentAnim() is None:
        if self.cur_anim == "RunCycle":
            return
        self.actor.loop("RunCycle")
        self.fade_in_anim("RunCycle", 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = "RunCycle"

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
        if self.cur_anim == "Idle":
            self.start_idle()

    def exit_combat(self):
        self.idle_anim = "Idle"
        if self.cur_anim == "CombatStance":
            self.start_idle()

    def do_attack(self):
        anim = "PunchRight"
        self.actor.play(anim)
        anim_control = self.actor.get_anim_control(anim)
        num_frames = anim_control.get_num_frames()
        t = num_frames / 24
        def start():
            self.fade_in_anim(anim, 0.2)
            self.fade_out_anim(self.cur_anim, 0.2)
        def end():
            self.fade_in_anim(self.cur_anim, 0.2)
            self.fade_out_anim(anim, 0.2)
        s = Sequence(start, Wait(t), end)
        s.start()

    def fade_in_anim(self, name, t):
        prev_w = 0
        if name in self.fade_out_anims:
            prev_w = self.fade_out_anims[name][1]
            del self.fade_out_anims[name]
        self.fade_in_anims[name] = (t, prev_w)

    def fade_out_anim(self, name, t):
        prev_w = 1
        if name in self.fade_in_anims:
            prev_w = self.fade_in_anims[name][1]
            del self.fade_in_anims[name]
        self.fade_out_anims[name] = (t, prev_w)
