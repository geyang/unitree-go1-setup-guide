
import numpy as np
import os
from datetime import datetime
import copy
import time
import pickle as pkl
import isaacgym
import torch
from legged_gym.envs import *


def class_to_dict(obj) -> dict:
    if not  hasattr(obj,"__dict__"):
        return obj
    result = {}
    for key in dir(obj):
        if key.startswith("_") or key == "terrain":
            continue
        element = []
        val = getattr(obj, key)
        if isinstance(val, list):
            for item in val:
                element.append(class_to_dict(item))
        else:
            element = class_to_dict(val)
        result[key] = element
    return result

def export_policy_as_jit(actor_critic, path):
    os.makedirs(path, exist_ok=True)
    path = os.path.join(path, 'policy_1.pt')
    model = copy.deepcopy(actor_critic.actor).to('cpu')
    traced_script_module = torch.jit.script(model)
    traced_script_module.save(path)

def export_rma_policy_as_jit(actor_critic, path):
    os.makedirs(path, exist_ok=True)
    adaptation_module_path = os.path.join(path, 'adaptation_module.pt')
    body_path = os.path.join(path, 'body.pt')
    adaptation_module = copy.deepcopy(actor_critic.adaptation_module).to('cpu')
    body_model = copy.deepcopy(actor_critic.actor_body).to('cpu')
    traced_script_adaptation_module = torch.jit.script(adaptation_module)
    traced_script_body_module = torch.jit.script(body_model)
    traced_script_adaptation_module.save(adaptation_module_path)
    traced_script_body_module.save(body_path)

def export_rma_disentangled_policy_as_jit(actor_critic, path):
    os.makedirs(path, exist_ok=True)

    for i, adaptation_module in enumerate(actor_critic.adaptation_modules):
        adaptation_module_path = os.path.join(path, f'adaptation_module_{i}.pt')
        adaptation_module = copy.deepcopy(adaptation_module).to('cpu')
        traced_script_adaptation_module = torch.jit.script(adaptation_module)
        traced_script_adaptation_module.save(adaptation_module_path)

    body_path = os.path.join(path, 'body.pt')
    body_model = copy.deepcopy(actor_critic.actor_body).to('cpu')
    traced_script_body_module = torch.jit.script(body_model)
    traced_script_body_module.save(body_path)

def export_cse_policy_as_jit(actor_critic, path):
    os.makedirs(path, exist_ok=True)

    adaptation_module_path = os.path.join(path, f'adaptation_module.pt')
    adaptation_module = copy.deepcopy(actor_critic.adaptation_module).to('cpu')
    traced_script_adaptation_module = torch.jit.script(adaptation_module)
    traced_script_adaptation_module.save(adaptation_module_path)

    body_path = os.path.join(path, 'body.pt')
    body_model = copy.deepcopy(actor_critic.actor_body).to('cpu')
    traced_script_body_module = torch.jit.script(body_model)
    traced_script_body_module.save(body_path)

def construct_observation_encoder(env_cfg):
    # we also need to encode heightmap info, etc
    env_vars = vars(env_cfg.env)
    assert "num_observations" in env_vars.keys()
    return env_vars


def bundle_for_deployment(experiment_name, label, jumper=False):

    # load policy
    from legged_gym.envs.base.legged_robot_config import LeggedRobotCfg
    from legged_gym.envs.mini_cheetah.mini_cheetah_config import config_mini_cheetah
    from legged_gym.envs.go1.go1_config import config_go1
    # from legged_gym.scripts.helpers import class_to_dict

    config_go1(LeggedRobotCfg)

    from ml_logger import logger
    logger.configure(prefix=experiment_name)



    input(logger.glob("*"))
    params = logger.load_pkl("parameters.pkl")
    print(params)
    alg_name = params[0]["kwargs"]["Args.alg_name"]
    if alg_name == "rma":
        from legged_rl.rma_disentangled import ActorCriticRMA
        from legged_gym.envs.wrappers.rma_wrapper import RMAWrapper
        from legged_rl.rma_disentangled.actor_critic_rma import AC_Args
    elif alg_name == "cse":
        from legged_rl.concurrent_se import ActorCriticRMA
        from legged_gym.envs.wrappers.rma_wrapper import RMAWrapper
        from legged_rl.concurrent_se.actor_critic_rma import AC_Args
    else:
        print(f"Unknown alg: {alg_name} !")
        return 0
    AC_Args._update(params[0]['kwargs'])
    LeggedRobotCfg.env._update(params[0]['kwargs'])
    LeggedRobotCfg.commands._update(params[0]['kwargs'])
    LeggedRobotCfg.control._update(params[0]['kwargs'])
    LeggedRobotCfg.init_state._update(params[0]['kwargs'])
    #input(AC_Args.adaptation_module_hidden_dims)
    LeggedRobotCfg.env.num_observations = 63


    actor_critic = ActorCriticRMA(
        num_obs=LeggedRobotCfg.env.num_observations,
        num_privileged_obs=LeggedRobotCfg.env.num_privileged_obs,
        num_obs_history=LeggedRobotCfg.env.num_observations * \
                        LeggedRobotCfg.env.num_observation_history,
        num_actions=LeggedRobotCfg.env.num_actions)

    weights = logger.load_torch("checkpoints/ac_weights_last.pt")
    # weights = logger.load_torch("checkpoints/ac_weights_001600.pt")
    actor_critic.load_state_dict(state_dict=weights)
    #actor_critic.to(env.device)

    policy = actor_critic.act_inference

    #if "rma" in experiment_name or "control_frequency" in experiment_name:
    obs = {"obs": torch.zeros((1, LeggedRobotCfg.env.num_observations)), "obs_history": torch.zeros((1, LeggedRobotCfg.env.num_observations*LeggedRobotCfg.env.num_observation_history)), "privileged_obs": None}
    #else:
    #    obs = torch.zeros((1, LeggedRobotCfg.env.num_observations))
    tstart = time.time()
    num_steps = 1000
    for i in range(num_steps):
        actions = policy(obs)
    print(f"frequency: {num_steps / (time.time()-tstart)} Hz")

    # we want: the jit file; the env configuration in dict form
    #env_cfg = load_dict["env_cfg"]
    #env_cfg_encoding = construct_observation_encoder(env_cfg)
    #print(env_cfg_encoding)
    env_cfg_encoding = class_to_dict(LeggedRobotCfg)


    datetime = time.strftime("%Y_%m_%d-%H_%M")
    path = f"../models/{label}_{datetime}/"
    #if "rma" in experiment_name or "control_frequency" in experiment_name:
    #export_rma_policy_as_jit(actor_critic, path=path)
    if alg_name == "rma":
        export_rma_disentangled_policy_as_jit(actor_critic, path=path)
    elif alg_name == "cse":
        export_cse_policy_as_jit(actor_critic, path=path)
    else:
        print("Could not export policy, unknown architecture!!")



    with open(path+"data.pkl", 'wb') as file:
        pkl.dump({"env_cfg": env_cfg_encoding,
                  }, file)

    print("Done")


if __name__ == '__main__':
    #experiment_name = "legged-gym/legged-gym/2022/01-07/rss_2022/velocity_obs_impact/velocity_obs_impact/velocity_obs_impact_sweep/VelocityTrackingEasyEnv/alg_ppo/ob_vel_False/100"
    #experiment_name = "legged-gym/legged-gym/2022/01-17/rss_2022/rma_impact/rma_impact_yaw/rma_impact_exclusive_sampling/VelocityTrackingEasyEnv/alg_rma/exccmd2_True/200"
    # = "legged-gym/legged-gym/2022/01-14/rss_2022/rma_impact/rma_impact_yaw/rma_impact_yaw_sweep_max/VelocityTrackingEasyEnv/alg_rma/300"
    #experiment_name = "legged-gym/legged-gym/2022/01-20/rss_2022/rma_impact/rma_impact_yaw/rma_impact_distributional_sampling/VelocityTrackingEasyEnv/alg_rma/clean_curriculum_logging_test5_True/fwthresh_0.6/yawthresh_0.5/100"
    #experiment_name = "legged-gym/legged-gym/2022/01-20/rss_2022/rma_impact/rma_impact_yaw/rma_impact_distributional_sampling/VelocityTrackingEasyEnv/alg_rma/clean_curriculum_logging_test5_True/fwthresh_0.6/yawthresh_0.5/100"
    #experiment_name = "legged-gym/legged-gym/2022/01-21/rss_2022_submission/curriculum/curriculum_evaluation/curriculum_evaluation_sweep/alg_rma/distr/exc_False/fw_lim_0.6/yaw_lim_0.5/100"
    experiment_name = "legged-gym/legged-gym/2022/01-21/rss_2022_submission/curriculum/curriculum_evaluation/curriculum_evaluation_sweep/alg_rma/distr/exc_False/fw_lim_0.8/yaw_lim_0.7/500"
    #experiment_name = "legged-gym/legged-gym/2022/01-21/rss_2022_submission/baselines/rma/rma_ppo_comparison/alg_ppo/distr/exc_False/fw_lim_0.6/yaw_lim_0.5/200"
    
    # 1/25
    experiment_name = "legged-gym/legged-gym/2022/01-05/rss_2022/rma_impact/rma_impact/rma_impact_sweep/VelocityTrackingEasyEnv/alg_rma/100/"
    #experiment_name = "legged-gym/legged-gym/2022/01-05/rss_2022/bandwidth_limits/control_frequency/control_frequency/control_frequency_sweep/VelocityTrackingEasyEnv/freq_50.00Hz/200/"
    
    # previous branch
    #experiment_name = "legged-gym/legged-gym/2022/01-07/rss_2022/velocity_obs_impact/velocity_obs_impact/velocity_obs_impact_sweep/VelocityTrackingEasyEnv/alg_ppo/ob_vel_False/100"
    experiment_name = "legged-gym/legged-gym/2022/01-17/rss_2022/rma_impact/rma_impact_yaw/rma_impact_exclusive_sampling/VelocityTrackingEasyEnv/alg_rma/exccmd2_True/200"
    # = "legged-gym/legged-gym/2022/01-14/rss_2022/rma_impact/rma_impact_yaw/rma_impact_yaw_sweep_max/VelocityTrackingEasyEnv/alg_rma/300"

    # Unitree Model v0
    experiment_name = "legged-gym/legged-gym/2022/02-03/eccv_2022/go1_blind/sweeps/debug/rma/w/300"
    # Unitree Model v1
    experiment_name = "legged-gym/legged-gym/2022/02-09/eccv_2022/go1_blind/sweeps/debug/rma/u/300"

    experiment_name = "legged-gym/legged-gym/2022/02-23/eccv_2022/go1_blind/sweeps/nominal/rma/400"
    experiment_name = "legged-gym/legged-gym/2022/02-23/eccv_2022/go1_blind/sweeps/nominal/rma/100"

    experiment_name = "legged-gym/legged-gym/2022/02-27/eccv_2022/go1_blind/sweeps/low_friction/rma/300"
    experiment_name = "legged-gym/legged-gym/2022/02-27/eccv_2022/go1_blind/sweeps/student_lr/rma/lr_0.001/substeps_4/adahid_[256, 128]/100"
    experiment_name = "legged-gym/legged-gym/2022/02-27/eccv_2022/go1_blind/sweeps/student_lr/rma/lr_0.0001/substeps_10/adahid_[256, 128]/100" # 226 DATA COLLECTION


    experiment_name = "legged-gym/legged-gym/2022/03-03/eccv_2022/jumping_go1/sweeps/impulse_jump_commands/rma/bhrange_[-0.2, 0.2]/jdur_0.3/jint_2.0/200" # body height control
    experiment_name = "legged-gym/legged-gym/2022/03-02/eccv_2022/go1_blind/sweeps/privileged_info_sweep/all_but_motors/100" # all but motors
    experiment_name = "legged-gym/legged-gym/2022/03-02/eccv_2022/go1_blind/sweeps/privileged_info_sweep/terrain/200" # terrain params only
    experiment_name = "legged-gym/legged-gym/2022/03-02/eccv_2022/go1_blind/sweeps/privileged_info_sweep/motor_strength/100" # motors only


    experiment_name = "legged-gym/legged-gym/2022/03-04/eccv_2022/jumping_go1/sweeps/disentangled_latents_jumper/disentangle_motor_strength_no_payload_com/300" # motors only
    experiment_name = "legged-gym/legged-gym/2022/03-03/eccv_2022/go1_blind/sweeps/disentangled_latents/disentangle_motor_strength/200"
    experiment_name = "legged-gym/legged-gym/2022/03-03/eccv_2022/go1_blind/sweeps/disentangled_latents/disentangle_all/200"
    experiment_name = "legged-gym/legged-gym/2022/03-04/eccv_2022/jumping_go1/sweeps/disentangled_latents_jumper/disentangle_motor_strength/300"
    experiment_name = "legged-gym/legged-gym/2022/03-09/eccv_2022/go1_blind/sweeps/dr_comparison_full/rma/privileged_info_large_latent/300"

    experiment_name = "legged-gym/legged-gym/2022/03-20/eccv_2022/jumping_go1/sweeps/disentangled_latents_jumper/small_push/100"
    experiment_name = "legged-gym/legged-gym/2022/03-21/eccv_2022/jumping_go1/sweeps/disentangled_latents_jumper_long/no_push_12k/300"
    experiment_name = "legged-gym/legged-gym/2022/03-30/eccv_2022/jumping_go1/sweeps/privileged_state_sweep/all/400"
    experiment_name = "legged-gym/legged-gym/2022/03-30/eccv_2022/jumping_go1/sweeps/privileged_state_randsweep/no_rand/tnm_0.0/300"
    experiment_name = "legged-gym/legged-gym/2022/03-31/eccv_2022/jumping_go1/sweeps/gravity_sweep/mid_dgravity/300"
    experiment_name = "legged-gym/legged-gym/2022/04-01/eccv_2022/jumping_go1/sweeps/gravity_sweep_low_speed/large_dgravity/300"
    experiment_name = "legged-gym/legged-gym/2022/04-02/eccv_2022/jumping_go1/sweeps/gravity_sweep_low_speed_standstill/small_dgravity/ss_-0.01/fcf_-0.1/100"
    experiment_name = "legged-gym/legged-gym/2022/04-03/eccv_2022/jumping_go1/sweeps/body_stability_sweep/no_Kprand_vel/ss_-1.0/fcf_-0.01/200"
    experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/no_dgravity/ss_0.0/fcf_-0.01/300"
    experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/baseline/ss_0.0/fcf_-0.01/300"
    experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/large_latent/ss_0.0/fcf_-0.01/100"
    # experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/no_dgravity/ss_0.0/fcf_-0.01/100"  # nice gait, but drift
    # experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/no_extras/ss_0.0/fcf_-0.01/100" # no drift, but the occasional weird swaying/lunge
    # experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations/no_vel/ss_0.0/fcf_-0.01/300" # drift
    experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations_2/lower_body/ss_0.0/fcf_-0.01/300"  # no drift but drags feet/sags
    experiment_name = "legged-gym/legged-gym/2022/04-04/eccv_2022/jumping_go1/sweeps/gravity_sweep_er_ablations_2/lower_body_no_vel/ss_0.0/fcf_-0.01/300"
    experiment_name = "locomotion/locomotion/2022/05-06/eccv_2022/go1_blind_gait_adaptation/sweeps/trot_pronk_duration/r20/gfs_100.0/gvs_10.0/kappa_0.07/600"
    experiment_name = "locomotion/locomotion/2022/05-13/eccv_2022/go1_blind_gait_adaptation/sweeps/trot_pronk_duration/rand_frictions_indep_only/gfs_100.0/gvs_10.0/kappa_0.07/100"
    experiment_name = "locomotion/locomotion/2022/05-13/eccv_2022/go1_blind_gait_adaptation/sweeps/trot_pronk_duration_slow_and_robust/rand_frictions_indep_only/gfs_100.0/gvs_10.0/kappa_0.07/100"
    experiment_name = "locomotion/locomotion/2022/05-13/eccv_2022/go1_blind_gait_adaptation/sweeps/trot_pronk_duration_robust/fixed_base_height/gfs_100.0/gvs_10.0/kappa_0.07/100"
    experiment_name = "locomotion/locomotion/2022/05-16/eccv_2022/go1_ji22_rewards/sweeps/domain_rand_rss/08.55.50/srn_0.2/300"
    experiment_name = "locomotion/locomotion/2022/05-16/eccv_2022/go1_ji22_rewards/sweeps/velocity_curriculum/21.29.24/srn_0.2/100"
    experiment_name = "locomotion/locomotion/2022/05-17/eccv_2022/go1_ji22_rewards/sweeps/variable_gait/08.20.03/csf_0.5/csv_4.0/srn_0.2/300"
    experiment_name = "locomotion/locomotion/2022/05-17/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs/half_ns2/gfs_100.0/gvs_10.0/kappa_0.07/200"
    experiment_name = "locomotion/locomotion/2022/05-17/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_highspeed/half_ns2/gfs_100.0/gvs_10.0/kappa_0.07/300"
    experiment_name = "locomotion/locomotion/2022/05-17/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_v2_decoder_velocity/16.04.23/gfs_100.0/gvs_10.0/kappa_0.07/100"
    experiment_name = "locomotion/locomotion/2022/05-17/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_highspeed_decoder_velocity/22.01.26/gfs_100.0/gvs_10.0/kappa_0.07/300"
    experiment_name = "locomotion/locomotion/2022/05-18/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_and_vels/12.55.32/gfs_100.0/gvs_10.0/kappa_0.07/200"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_dr/16.22.26/gfs_100.0/gvs_10.0/kappa_0.07/200"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_dr_wide_stance/18.46.13/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_dr_wide_stance/18.46.13/stance_2.0/200"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_wide_stance/19.44.05/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance/21.12.18/stance_2.0/300"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance/21.12.18/stance_1.0/200"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_highspeed_wide_stance/22.03.25/stance_1.0/200"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_offsets/22.22.43/stance_2.0/300"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_motor_strength/22.23.03/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_gravity/22.23.35/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-20/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_com_displacement/22.23.55/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_observe_com_displacement/13.08.05/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_observe_com_displacement_gravity/13.11.41/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_offsets_strength/13.09.15/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_merged_jisiekmann_rewards/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_ablate_offsets_strength_observe_gravity/13.10.23/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_concurrent_se/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance/13.47.18/stance_2.0/100"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_concurrent_se/sweeps/combo_runs_decoder_binary_foot_frictions_extradr_v2_wide_stance_observe_gravity_ablate_dr/14.41.34/stance_2.0/300"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward/15.51.00/csf_4.0/csv_4.0/stance_1.0/200"
    experiment_name = "locomotion/locomotion/2022/05-21/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep/17.32.12/srn_0.02/stance_1.0/100"
    experiment_name = "locomotion/locomotion/2022/05-22/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_highspeed/08.55.10/srn_0.05/stance_1.0/300"
    experiment_name = "locomotion/locomotion/2022/05-22/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_frictionest_estimation_bonus_nonbinary/17.13.02/estimation_bonus_-1/300"
    experiment_name = "locomotion/locomotion/2022/05-22/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_frictionest_nonbinary_contactest/18.16.27/estimation_bonus_0.0/200"
    experiment_name = "locomotion/locomotion/2022/05-22/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_frictionest_estimation_bonus_nonbinary/17.13.02/estimation_bonus_-1/100"
    experiment_name = "locomotion/locomotion/2022/05-22/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_highspeed/08.55.10/srn_0.05/stance_1.0/300"
    experiment_name = "locomotion/locomotion/2022/05-23/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_highspeed_friction_estimation_low_frequency_and_bound/19.25.17/srn_0.05/stance_1.0/300"
    experiment_name = "locomotion/locomotion/2022/05-23/eccv_2022/go1_concurrent_se/sweeps/cse_sweep_gait_reward_jistyleclip_penalty_sweep_frictionest_nonbinary_contactest_fixed_badht/14.11.11/estimation_bonus_0.0/300"

    label = "20220320_jumper_large_latent_100"
    label = "20220321_jumper_large_latent_long_100"
    label = "20220330_jumper_moreprivileged_midgravity_300"
    label = "20220330_jumper_oriented_large_gravity_300"
    label = "20220402_standstill_contactforce_100"
    label = "20220403_nokprand_200"
    label = "20220404_nogravity_300"
    label = "20220404_baselinef_300"
    label = "20220404_largelatent_200"
    label = "20220404_nogravityf_100"
    # label = "20220404_noextras_100"
    #label = "20220404_novel_300"
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
    label = "20220517_jisiekmann_highspeed_300"
    label = "20220517_decoder_obvel_100"
    label = "20220517_decoder_obvelfixed_highspeed_300"
    label = "20220519_decoder_frictions_and_vels_200"
    label = "20220520_decoder_frictions_dr_b_200"
    label = "20220520_stance2_v2_100"
    label = "20220520_stance2_200"
    label = "20220520_stance2_extradr_200"
    label = "20220520_stance2_extradr2_200"
    label = "20220520_stance1_extradr2_later_200"
    label = "20220520_stance1_extradr2_highspeed_200"
    label = "20220521_ablate_offsets_200"
    label = "20220521_ablate_motor_strength_100"
    label = "20220521_ablate_gravity_100"
    label = "20220521_ablate_com_displacement_100"
    label = "20220521_ablate_observe_com_displacement_100"
    label = "20220521_ablate_observe_com_displacement_gravity_100"
    label = "20220521_ablate_offsets_strength_100"
    label = "20220521_ablate_offsets_strength_observe_gravity_100"
    label = "20220521_concurrent_base_100"
    label = "20220521_concurrent_ablate_dr_100"
    label = "20220521_concurrent_bigcontact_200" # awesome policy to demo!!!!
    label = "20220521_concurrent_jistyleclip_200"
    label = "20220522_concurrent_jistyleclip_highspeed_300"
    label = "20220522_concurrent_jistyleclip_highspeed_300_compat"  # really awesome policy to demo, outdoor videos from 5/22!!!
    label = "20220522_concurrent_jistyleclip_estimation_bonus_300"
    label = "20220523_concurrent_platform_trained_200"
    label = "20220523_concurrent_jistyleclip_estimation_bonus_100"
    label = "20220522_concurrent_jistyleclip_highspeed_300_4k" # demo policy, outdoor videos from 5/23
    label = "20220524_concurrent_with_bounding"
    label = "20220524_blind_robust_platformer_300"

    bundle_for_deployment(experiment_name, label, jumper=True)
