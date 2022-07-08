import glob
import pickle as pkl
import lcm
import sys

from jetson_deploy.utils.deployment_runner import DeploymentRunner
from jetson_deploy.envs.lcm_agent import LCMAgent
from jetson_deploy.utils.cheetah_state_estimator import StateEstimator
from jetson_deploy.utils.command_profile import *

import pathlib

lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=255")


def load_and_run_policy(label, experiment_name, probe_policy_label=None, max_vel=1.0, max_vel_probe=1.0):
    # load agent
    dirs = glob.glob(f"../models/{label}_*")
    logdir = sorted(dirs)[0]
    with open(logdir+"/data.pkl", 'rb') as file:
        cfg = pkl.load(file)['env_cfg']


    se = StateEstimator(lc, use_vicon=False)

    control_dt = 0.02
    command_profile = RCControllerProfile(dt=control_dt, state_estimator=se, x_scale=max_vel, y_scale=0.6, yaw_scale=max_vel, probe_vel_multiplier=(max_vel_probe / max_vel))
    #command_profile = RCControllerProfileAccel(dt=control_dt, state_estimator=se, x_scale=4.0, y_scale=0.6, yaw_scale=4.0)
    # command_profile = ConstantAccelerationProfile(dt=isaac_agent.dt, max_speed=max_vel, accel_time=2.0, zero_buf_time=1.0)

    R1_command_profile = ElegantForwardProfile(
        dt=control_dt, max_speed=max_vel, zero_buf_time=0.0, accel_time=0.5, duration=2.0, deaccel_time=0.5)
    #command_profile.add_triggered_command(button_idx=3, command_profile=R1_command_profile)

    #command_profile = ElegantYawProfile(
    #    dt=control_dt, max_speed=max_vel, zero_buf_time=1.0, accel_time=1.0, duration=5.0, deaccel_time=0.5, yaw_rate=yaw_rate)
    # cfg["init_state"]["default_joint_angles"]["FL_hip_joint"] = 0.15
    # cfg["init_state"]["default_joint_angles"]["RL_hip_joint"] = 0.15
    # cfg["init_state"]["default_joint_angles"]["FR_hip_joint"] = -0.15
    # cfg["init_state"]["default_joint_angles"]["RR_hip_joint"] = -0.15
    hardware_agent = LCMAgent(cfg, se, command_profile)
    se.spin()

    # load policy
    input(label)

    from jetson_deploy.envs.rma_wrapper import RMAWrapper
    hardware_agent = RMAWrapper(hardware_agent)

    # policy = load_policy(logdir, policy_class="disentangle")
    policy = load_policy(logdir)

    if probe_policy_label is not None:
        # load agent
        dirs = glob.glob(f"../models/{probe_policy_label}_*")
        probe_policy_logdir = sorted(dirs)[0]
        with open(probe_policy_logdir + "/data.pkl", 'rb') as file:
            probe_cfg = pkl.load(file)['env_cfg']
        probe_policy = load_policy(probe_policy_logdir)

    # load runner
    root = f"{pathlib.Path(__file__).parent.resolve()}/../../logs/"
    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    deployment_runner = DeploymentRunner(experiment_name=experiment_name, se=None,
                                         log_root=f"{root}/{experiment_name}")
    deployment_runner.add_control_agent(hardware_agent, "hardware_closed_loop")
    deployment_runner.add_policy(policy)
    if probe_policy_label is not None:
        deployment_runner.add_probe_policy(probe_policy, probe_cfg)
    deployment_runner.add_command_profile(command_profile)

    if len(sys.argv) >= 2:
        max_steps = int(sys.argv[1])
    else:
        max_steps = 10000000
    print(f'max steps {max_steps}')

    deployment_runner.run(max_steps=max_steps)

def load_policy(logdir, policy_class="cse"):
    if policy_class == "cse":
        body = torch.jit.load(logdir + '/body.pt')
        import os
        adaptation_module = torch.jit.load(logdir+'/adaptation_module.pt')

        def policy(obs, info):
            i = 0
            latent = adaptation_module.forward(obs["obs_history"].to('cpu'))
            action = body.forward(torch.cat((obs["obs_history"].to('cpu'), latent), dim=-1))
            info['latent'] = latent
            return action
    elif policy_class == "disentangle":
        body = torch.jit.load(logdir + '/body.pt')
        import os
        adaptation_modules = []
        adaptation_modules_names = [f for f in os.listdir(logdir) if f[:5] == 'adapt']
        print(adaptation_modules_names)
        for file in adaptation_modules_names:
            adaptation_modules += [torch.jit.load(logdir + f'/{file}')]
        print(adaptation_modules)

        def policy(obs, info):
            i = 0
            latents = []
            for adaptation_module in adaptation_modules:
                latents += [adaptation_module.forward(obs["obs_history"].to('cpu'))]
            latent = torch.cat(latents, dim=-1)
            action = body.forward(torch.cat((obs["obs"].to('cpu'), latent), dim=-1))
            info['latent'] = latent
            return action
    elif "rma" or "v0" in label:
        body = torch.jit.load(logdir+'/body.pt')
        adaptation_module = torch.jit.load(logdir+'/adaptation_module.pt')
        def policy(obs, info):
            latent = adaptation_module.forward(obs["obs_history"].to('cpu'))
            action = body.forward(torch.cat((obs["obs"].to('cpu'), latent), dim=-1))
            info['latent'] = latent
            return action
    else:
        raise Exception(f"Unknown policy class: {policy_class}")

    return policy


if __name__ == '__main__':
    # label = "ppo_no_vel_blind"
    # label = "rma_exclusive_sampling"
    # label = "rma_curriculum65"
    # label = "unitree_v1"
    # label = "unitree_v2_s1"
    # label = "unitree_v3_s3_20220227_rma"
    label = "unitree_v3_h128_s1_20220227_rma"
    label = "unitree_v3_h128lr4_s1_20220227_rma"
    # label = "220302_allbutmotors"
    # label = "220302_bodyheight"
    #label = "220302_justmotors"
    #label = "220304_disentangle_motor_strength_no_payload_com_300"
    #label = "220302_disentangle_motor_strength_200" # this one worked really nicely!
    #label = "220302_disentangle_all_200" # doesnt work well -- com was forced into a single latent :/
    #label = "20220304_disentangle_motor_strength_jumper"
    #label = "20220309_large_latent"
    label = "20220309_large_latent_300"
    label = "20220320_jumper_large_latent_100"
    label = "20220321_jumper_large_latent_long_100"
    label = "20220330_jumper_moreprivileged_full_400"
    label = "20220330_jumper_moreprivileged_full_tn4smallpd_300"
    label = "20220330_jumper_moreprivileged_full_tn0smallpd_300"
    label = "20220330_jumper_moreprivileged_full_tn0nopd_300"
    label = "20220330_jumper_moreprivileged_midgravity_300"
    label = "20220330_jumper_oriented_large_gravity_300"
    label = "20220402_standstill_contactforce_100"
    label = "20220404_nogravity_300"
    label = "20220404_baselinef_300"
    label = "20220404_largelatent_200"
    label = "20220404_nogravityf_300"
    label = "20220404_noextras_300"
    label = "20220404_novel_300"
    label = "20220404_noextras_100"
    #label = "20220403_nokprand_300"
    #label = "20220403_nokprand_200"
    label = "20220404_nogravityf_100"
    label = "20220404_largelatent_100"
    label = "20220404_lowerbody_300"
    label = "20220404_novel2_300"
    label = "20220511_multigait_600"
    label = "20220513_multigait_100"
    label = "20220513_gravrobust_multigait_100"
    label = "20220513_gravrobustfast_multigait_100"
    label = "20220516_ji22rewards_robust_300"
    label = "20220517_ji22rewards_fast_100"
    label = "20220517_ji22rewards_gaitadaptation_300"
    label = "20220517_jisiekmann_half_200"
    # label = "20220517_jisiekmann_highspeed_300"
    # label = "20220517_decoder_obvel_100"
    # label = "20220517_decoder_obvelfixed_highspeed_300"
    label = "20220519_decoder_frictions_and_vels_200"
    label = "20220520_decoder_frictions_dr_200"
    label = "20220520_decoder_frictions_dr_b_200"
    label = "20220520_stance2_100"
    label = "20220520_stance2_v2_100"
    label = "20220520_stance2_200"
    label = "20220520_stance2_extradr_200"
    label = "20220520_stance2_extradr2_200"
    label = "20220520_stance1_extradr2_200"
    label = "20220520_stance1_extradr2_later_200"
    label = "20220520_stance1_extradr2_highspeed_200"
    label = "20220521_ablate_offsets_200"
    label = "20220521_ablate_motor_strength_100"
    label = "20220521_ablate_gravity_100"
    label = "20220521_ablate_com_displacement_100"
    label = "20220521_ablate_observe_com_displacement_100" # OK
    label = "20220521_ablate_observe_com_displacement_gravity_100" # OK
    label = "20220521_ablate_offsets_strength_100" #
    label = "20220521_ablate_offsets_strength_observe_gravity_100" # less stable
    label = "20220521_concurrent_base_100"
    label = "20220521_concurrent_ablate_dr_100"
    label = "20220521_concurrent_bigcontact_200" # awesome policy to demo!!!
    label = "20220521_concurrent_jistyleclip_200"
    label = "20220522_concurrent_jistyleclip_highspeed_300"
    label = "20220522_concurrent_jistyleclip_highspeed_300_compat"  # really awesome policy to demo, outdoor videos from 5/22!!!
    label = "20220522_concurrent_jistyleclip_estimation_bonus_300" # friction estimation policy :)
    label = "20220523_concurrent_platform_trained_200"
    label = "20220523_concurrent_jistyleclip_estimation_bonus_100"
    label = "20220522_concurrent_jistyleclip_highspeed_300_4k"
    label = "20220524_concurrent_with_bounding"
    # label = "20220524_blind_robust_platformer_300"

    probe_policy_label = "20220523_concurrent_jistyleclip_estimation_bonus_100"
    probe_policy_label = "20220524_blind_robust_platformer_300"

    experiment_name = "20220524_morning_robust_platformer"

    # load_and_run_policy(label, experiment_name=label, max_vel=1.0, disentangle=True)
    load_and_run_policy(label, experiment_name=experiment_name, probe_policy_label=probe_policy_label, max_vel=4.0, max_vel_probe=1.0)
