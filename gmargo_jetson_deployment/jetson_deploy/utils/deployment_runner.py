# import isaacgym
# from isaacgym.gymapi import KeyboardInput
import copy
import time
import os

import numpy as np
import torch

from jetson_deploy.utils.logger import MultiLogger


class DeploymentRunner:
    def __init__(self, experiment_name="unnamed", se=None, log_root="."):
        self.agents = {}
        self.policy = None
        self.command_profile = None
        self.logger = MultiLogger()
        self.se = se
        self.vision_server = None

        self.log_root = log_root
        self.init_log_filename()
        self.control_agent_name = None
        self.command_agent_name = None

        self.triggered_commands = {i: None for i in range(4)} # command profiles for each action button on the controller
        self.button_states = np.zeros(4)

        self.is_currently_probing = False
        self.is_currently_logging = [False, False, False, False]

    def init_log_filename(self):
        datetime = time.strftime("%Y/%m_%d/%H_%M_%S")

        for i in range(100):
            try:
                os.makedirs(f"{self.log_root}/{datetime}_{i}")
                self.log_filename = f"{self.log_root}/{datetime}_{i}/log.pkl"
                return
            except FileExistsError:
                continue


    def add_open_loop_agent(self, agent, name):
        self.agents[name] = agent
        self.logger.add_robot(name, agent.env.cfg)

    def add_control_agent(self, agent, name):
        self.control_agent_name = name
        self.agents[name] = agent
        self.logger.add_robot(name, agent.env.cfg)

    def add_vision_server(self, vision_server):
        self.vision_server = vision_server

    def set_command_agents(self, name):
        self.command_agent = name

    def add_policy(self, policy):
        self.policy = policy

    def add_probe_policy(self, probe_policy, probe_cfg):
        self.probe_policy = probe_policy
        self.probe_cfg = probe_cfg

    def add_command_profile(self, command_profile):
        self.command_profile = command_profile


    def calibrate(self, wait=True):
        # first, if the robot is not in nominal pose, move slowly to the nominal pose
        for agent_name in self.agents.keys():
            if hasattr(self.agents[agent_name], "get_obs"):
                agent = self.agents[agent_name]
                agent.get_obs()
                joint_pos = agent.dof_pos
                nominal_joint_pos = agent.default_dof_pos

                if wait: input(f"CALIBRATE STARTING POSE {agent_name}...")
                cal_action = np.zeros((agent.num_envs, agent.num_actions))
                target_sequence = []
                target = joint_pos - nominal_joint_pos
                while np.max(np.abs(target)) > 0.01:
                    target -= np.clip(target, -0.05, 0.05)
                    target_sequence += [copy.deepcopy(target)]
                for target in target_sequence:
                    next_target = target
                    if isinstance(agent.cfg, dict):
                        hip_reduction = agent.cfg["control"]["hip_scale_reduction"]
                        action_scale = agent.cfg["control"]["action_scale"]
                    else:
                        hip_reduction = agent.cfg.control.hip_scale_reduction
                        action_scale = agent.cfg.control.action_scale

                    next_target[[0, 3, 6, 9]] /= hip_reduction
                    next_target = next_target / action_scale
                    cal_action[:, 0:12] = next_target
                    agent.step(torch.from_numpy(cal_action))
                    agent.get_obs()
                    time.sleep(0.05)

                if wait: input("STARTING POSE CALIBRATED...")

                for agent_name in self.agents.keys():
                    obs = self.agents[agent_name].reset()
                    if agent_name == self.control_agent_name:
                        control_obs = obs

        return control_obs


    def run(self, num_log_steps=1000000000, max_steps=100000000, logging=True):
        assert self.control_agent_name is not None, "cannot deploy, runner has no control agent!"
        assert self.policy is not None, "cannot deploy, runner has no policy!"
        assert self.command_profile is not None, "cannot deploy, runner has no command profile!"

        # TODO: add basic test for comms

        for agent_name in self.agents.keys():
            obs = self.agents[agent_name].reset()
            if agent_name == self.control_agent_name:
                control_obs = obs

        control_obs = self.calibrate(wait=True)

        # now, run control loop

        try:
            for i in range(max_steps):

                policy_info = {}
                if self.is_currently_probing:
                    action = self.probe_policy(control_obs, policy_info)
                else:
                    action = self.policy(control_obs, policy_info)

                # set command
                # command, reset_timer = self.command_profile.get_command(self.agents[self.control_agent_name].timestep * self.agents[self.control_agent_name].dt, probe=self.is_currently_probing)
                # if reset_timer:
                #     self.agents[agent_name].reset_gait_indices()
                #
                # #print(command)
                # for agent_name in self.agents.keys():
                #     self.agents[agent_name].commands[:, 0] = command[0]
                #     self.agents[agent_name].commands[:, 1] = command[1]
                #     self.agents[agent_name].commands[:, 2] = command[2]

                for agent_name in self.agents.keys():
                    obs, ret, done, info = self.agents[agent_name].step(action)

                    info.update(policy_info)
                    info.update({"observation": obs, "reward": ret, "done": done, "timestep": i,
                                 "time": i * self.agents[self.control_agent_name].dt, "action": action, "rpy": self.agents[self.control_agent_name].se.get_rpy(), "torques": self.agents[self.control_agent_name].torques})

                    # if self.vision_server is not None:
                        # depth_image_front = self.vision_server.get_depth_image(cam_id=1)
                        # rect_image_front = self.vision_server.get_rect_image(cam_id=1)
                        # raw_image_front = self.vision_server.get_raw_image(cam_id=1)
                        # depth_image_bottom = self.vision_server.get_depth_image(cam_id=0)
                        # rect_image_bottom = self.vision_server.get_rect_image(cam_id=0)
                        # raw_image_bottom = self.vision_server.get_raw_image(cam_id=0)
                        # info.update({"rect_image_front": rect_image_front, "raw_image_front": raw_image_front, "depth_image_front": depth_image_front,
                        #              "rect_image_bottom": rect_image_bottom, "raw_image_bottom": raw_image_bottom, "depth_image_bottom": depth_image_bottom})
                    # info.update({"raw_image_front": self.agents[self.control_agent_name].camera_image_front, "raw_image_front": raw_image_front, "depth_image_front": depth_image_front,
                    #              "rect_image_bottom": rect_image_bottom, "raw_image_bottom": raw_image_bottom, "depth_image_bottom": depth_image_bottom})

                    if logging: self.logger.log(agent_name, info)

                    if agent_name == self.control_agent_name:
                        control_obs, control_ret, control_done, control_info = obs, ret, done, info

                # check for logging command

                prev_button_states = self.button_states[:]
                self.button_states = self.command_profile.get_buttons()

                if self.command_profile.state_estimator.right_upper_switch_pressed:
                    if not self.is_currently_probing:
                        print("START LOGGING")
                        self.is_currently_probing = True
                        self.agents[self.control_agent_name].set_probing(True)
                        self.init_log_filename()
                        self.logger.reset()
                    else:
                        print("SAVE LOG")
                        self.is_currently_probing = False
                        self.agents[self.control_agent_name].set_probing(False)
                        # calibrate, log, and then resume control
                        control_obs = self.calibrate(wait=False)
                        self.logger.save(self.log_filename)
                        self.init_log_filename()
                        self.logger.reset()
                        time.sleep(1)
                        control_obs = self.agents[self.control_agent_name].reset()
                    self.command_profile.state_estimator.right_upper_switch_pressed = False

                for button in range(4):
                    if self.command_profile.currently_triggered[button]:
                        if not self.is_currently_logging[button]:
                            print("START LOGGING")
                            self.is_currently_logging[button] = True
                            self.init_log_filename()
                            self.logger.reset()
                    else:
                        if self.is_currently_logging[button]:
                            print("SAVE LOG")
                            self.is_currently_logging[button] = False
                            # calibrate, log, and then resume control
                            control_obs = self.calibrate(wait=False)
                            self.logger.save(self.log_filename)
                            self.init_log_filename()
                            self.logger.reset()
                            time.sleep(1)
                            control_obs = self.agents[self.control_agent_name].reset()

                if (self.button_states[2]):
                    control_obs = self.calibrate(wait=False)
                    while self.button_states[2]:
                        self.button_states = self.command_profile.get_buttons()
                        time.sleep(1)


                # if i % num_log_steps == 0:
                #     self.logger.save(self.log_filename)

            # finally, return to the nominal pose
            control_obs = self.calibrate(wait=False)
            self.logger.save(self.log_filename)

        except KeyboardInterrupt:
            self.logger.save(self.log_filename)
