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
