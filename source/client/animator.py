from ursina import *
import numpy as np
import quaternion


idle_anim = "Idle"
run_anim = "RunCycle"
combat_stance = "CombatStance"


class Anim(Entity):
    """Wrapper for Actor animation methods that encapsulates common animation sequences"""
    def __init__(self, actor):
        """actor: a Panda3D Actor object, which is the target of animation."""
        super().__init__()
        self.actor = actor
        self.idle = False
        self.in_combat = False
        self.actor.enableBlend()

        self.actor.makeSubpart("atk_right", ["shoulder.R", "shoulder.L"], excludeJoints=["bicep.L"],
                               overlapping=True)
        self.actor.makeSubpart("atk_left", ["shoulder.R", "shoulder.L"], excludeJoints=["bicep.R"],
                               overlapping=True)
        self.actor.makeSubpart("atk_base", ["hip"], excludeJoints=["shoulder.R", "shoulder.L"],
                               overlapping=True)
        # Nested dict mapping part to animation name to current animation weight
        self.anim_blends = {
            "modelRoot": {
                idle_anim: 0,
                run_anim: 0,
            },
            "atk_right": {
                "PunchRight": 0,
            },
            "atk_left": {
                "PunchLeft": 0,
            },
            "atk_base": {
                combat_stance: 0,
            },
        }
        self.fade_in_anims = dict()
        self.fade_out_anims = dict()

        self.end_run_cycle()

    def update(self):
        """Loop over fade in/fade out animations and update weights"""
        for part, anim_to_w in self.anim_blends.items():
            for anim, w in anim_to_w.items():
                if anim in self.fade_in_anims:
                    t = self.fade_in_anims[anim]
                    w = min(w + time.dt / t, 1)
                    self.set_anim_blend(anim, w, part=part)
                    if w == 1:
                        del self.fade_in_anims[anim]
                elif anim in self.fade_out_anims:
                    t = self.fade_out_anims[anim]
                    w = max(w - time.dt / t, 0)
                    self.set_anim_blend(anim, w, part=part)
                    if w == 0:
                        del self.fade_out_anims[anim]

    def start_run_cycle(self):
        if not self.idle:
            return
        self.idle = False
        self.actor.loop(run_anim)
        self.fade_in_anim(run_anim, 0.2)
        self.fade_out_anim(idle_anim, 0.2)
        self.fade_out_anim(combat_stance, 0.2)

    def end_run_cycle(self):
        if self.idle:
            return
        self.idle = True
        self.fade_out_anim(run_anim, 0.2)
        self.actor.loop(idle_anim)
        if not self.in_combat:
            self.fade_in_anim(idle_anim, 0.2)
        else:
            self.fade_in_anim(combat_stance, 0.2)

    def enter_combat(self):
        if self.in_combat:
            return
        self.in_combat = True
        self.actor.loop(combat_stance, partName="atk_base")
        if self.idle:
            self.fade_in_anim(combat_stance, 0.2)
            self.fade_out_anim(idle_anim, 0.2)
        self.fade_in_anim("PunchRight", 0.2)
        self.fade_in_anim("PunchLeft", 0.2)

    def exit_combat(self):
        if not self.in_combat:
            return
        self.in_combat = False
        self.fade_out_anim(combat_stance, 0.2)
        self.fade_out_anim("PunchRight", 0.2)
        self.fade_out_anim("PunchLeft", 0.2)
        if self.idle:
            self.fade_in_anim(idle_anim, 0.2)

    def do_attack(self, slot):
        if slot == "mh":
            anim = "PunchRight"
            grp = "atk_right"
        elif slot == "oh":
            anim = "PunchLeft"
            grp = "atk_left"
        self.actor.play(anim, partName=grp)

    def fade_in_anim(self, name, t):
        if name in self.fade_out_anims:
            del self.fade_out_anims[name]
        self.fade_in_anims[name] = t

    def fade_out_anim(self, name, t):
        if name in self.fade_in_anims:
            del self.fade_in_anims[name]
        self.fade_out_anims[name] = t

    def get_anim_blend(self, name, part="modelRoot"):
        return self.anim_blends.get(part, {}).get(name, 0)

    def set_anim_blend(self, name, w, part="modelRoot"):
        self.anim_blends[part][name] = w
        self.actor.setControlEffect(name, w, partName=part)
