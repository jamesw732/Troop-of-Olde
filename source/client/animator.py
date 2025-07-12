from ursina import *
import numpy as np
import quaternion

class Anim(Entity):
    """Wrapper for Actor animation methods that encapsulates common animation sequences"""
    def __init__(self, actor):
        """actor: a Panda3D Actor object, which is the target of animation."""
        super().__init__()
        self.actor = actor
        self.actor.loop("idle_pose")
        self.state = "idle"
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
        # if self.actor.getCurrentAnim() is None:
        if self.state != "running":
            self.actor.loop("RunCycle")
            self.fade_in_anim("RunCycle", 0.2)
            self.fade_out_anim("idle_pose", 0.2)
            self.state = "running"

    def end_run_cycle(self):
        if self.state != "idle":
            self.actor.loop("idle_pose")
            self.fade_in_anim("idle_pose", 0.2)
            self.fade_out_anim("RunCycle", 0.2)
            self.state = "idle"

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
