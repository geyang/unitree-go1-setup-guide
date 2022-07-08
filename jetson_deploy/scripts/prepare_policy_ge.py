import numpy as np
import os
from datetime import datetime
import copy
import time
import pickle as pkl
import isaacgym
import torch
from model_free_agility.envs import *


def class_to_dict(obj) -> dict:
    if not hasattr(obj, "__dict__"):
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
    # input(AC_Args.adaptation_module_hidden_dims)
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
    # actor_critic.to(env.device)

    policy = actor_critic.act_inference

    # if "rma" in experiment_name or "control_frequency" in experiment_name:
    obs = {"obs": torch.zeros((1, LeggedRobotCfg.env.num_observations)), "obs_history": torch.zeros(
        (1, LeggedRobotCfg.env.num_observations * LeggedRobotCfg.env.num_observation_history)), "privileged_obs": None}
    # else:
    #    obs = torch.zeros((1, LeggedRobotCfg.env.num_observations))
    tstart = time.time()
    num_steps = 1000
    for i in range(num_steps):
        actions = policy(obs)
    print(f"frequency: {num_steps / (time.time() - tstart)} Hz")

    # we want: the jit file; the env configuration in dict form
    # env_cfg = load_dict["env_cfg"]
    # env_cfg_encoding = construct_observation_encoder(env_cfg)
    # print(env_cfg_encoding)
    env_cfg_encoding = class_to_dict(LeggedRobotCfg)

    datetime = time.strftime("%Y_%m_%d-%H_%M")
    path = f"../models/{label}_{datetime}/"
    # if "rma" in experiment_name or "control_frequency" in experiment_name:
    # export_rma_policy_as_jit(actor_critic, path=path)
    if alg_name == "rma":
        export_rma_disentangled_policy_as_jit(actor_critic, path=path)
    elif alg_name == "cse":
        export_cse_policy_as_jit(actor_critic, path=path)
    else:
        print("Could not export policy, unknown architecture!!")

    with open(path + "data.pkl", 'wb') as file:
        pkl.dump({"env_cfg": env_cfg_encoding,
                  }, file)

    print("Done")


if __name__ == '__main__':
    import os

    os.environ['ML_LOGGER_ROOT'] = "http://escher.csail.mit.edu:8080"
    from ml_logger import logger

    experiment_name = "/geyang/rapid-locomotion/2022-06-02/train/164442-test"
    label = "20220524_blind_robust_platformer_300"

    bundle_for_deployment(experiment_name, label, jumper=True)
    print('I am done')
