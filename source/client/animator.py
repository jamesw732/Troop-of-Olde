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
        self.cur_anim = ""
        self.still_anim = idle_anim
        self.actor.enableBlend()

        all_joints = {joint.name for joint in self.actor.get_joints()}
        atk_right_joints = {"shoulder.R", "bicep.R", "forearm.R", "hand.R", "shoulder.L"}
        atk_left_joints = {"shoulder.L", "bicep.L", "forearm.L", "hand.L", "shoulder.R"}
        atk_base_joints = all_joints - (atk_right_joints | atk_left_joints)
        subpart_joints = {
            "atk_right": atk_right_joints,
            "atk_left": atk_left_joints,
            "atk_base": atk_base_joints,
        }
        for name, joints in subpart_joints.items():
            self.actor.makeSubpart(name, joints, overlapping=True)
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

        # all_anims = [idle_anim, run_anim, combat_stance, "PunchRight", "PunchLeft"]
        # self.anim_blends = {name: (0, "modelRoot") for name in all_anims}
        # # Nested dict mapping part name to animation name to fade-in time
        # self.fade_in_anims = {part: dict() for part in self.actor.getPartNames()}
        # # Nested dict mapping part name to animation name to fade-out time
        # self.fade_out_anims = {part: dict() for part in self.actor.getPartNames()}

        self.start_idle()

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
        """Starts run cycle"""
        if self.cur_anim == run_anim:
            return
        self.actor.loop(run_anim)
        self.fade_in_anim(run_anim, 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = run_anim

    def end_run_cycle(self):
        """Ends run cycle"""
        if self.still_anim == idle_anim:
            self.start_idle()
        elif self.still_anim == combat_stance:
            self.enter_combat()

    def start_idle(self):
        """Starts idle animation, which is either the Idle animation or CombatStance."""
        if self.cur_anim == idle_anim:
            return
        self.actor.loop(idle_anim)
        self.fade_in_anim(idle_anim, 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = idle_anim
        self.still_anim = idle_anim

    def enter_combat(self):
        if self.cur_anim == combat_stance:
            return
        self.actor.loop(combat_stance)
        self.fade_in_anim(combat_stance, 0.2)
        self.fade_out_anim(self.cur_anim, 0.2)
        self.cur_anim = combat_stance
        self.still_anim = combat_stance

    def do_attack(self, slot):
        if slot == "mh":
            anim = "PunchRight"
            grp = "atk_right"
        elif slot == "oh":
            anim = "PunchLeft"
            grp = "atk_left"
            return
        self.actor.play(anim, partName=grp)
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

    def get_anim_blend(self, name, part="modelRoot"):
        return self.anim_blends.get(part, {}).get(name, 0)

    def set_anim_blend(self, name, w, part="modelRoot"):
        self.anim_blends[part][name] = w
        self.actor.setControlEffect(name, w, partName=part)
