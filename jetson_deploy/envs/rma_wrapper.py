# import isaacgym

# assert isaacgym, "import isaacgym before pytorch"
import torch


class RMAWrapper:
    def __init__(self, env):
        self.env = env

        if isinstance(self.env.cfg, dict):
            if "num_observation_history" in self.env.cfg["env"].keys():
                self.obs_history_length = self.env.cfg["env"][
                    "num_observation_history"]  # TODO: We want this to be longer but it tends to fill up the GPU memory. Need to fix the handling, avoid redundancy in RMA RolloutStorage
            else:
                self.obs_history_length = 15
        else:
            if hasattr(self.env.cfg.env, "rma_obs_history_length"):
                self.obs_history_length = self.env.cfg.env.rma_obs_history_length
            else:
                self.obs_history_length = 15
        self.num_obs_history = self.obs_history_length * self.env.num_obs
        self.obs_history = torch.zeros(self.env.num_envs, self.num_obs_history, dtype=torch.float,
                                       device=self.env.device, requires_grad=False)
        self.num_privileged_obs = self.env.num_privileged_obs

    def step(self, action):
        # privileged information is concatenated to the observation, and observation history is stored in info
        obs, rew, done, info = self.env.step(action)
        privileged_obs = info["privileged_obs"]

        self.obs_history = torch.cat((self.obs_history[:, self.env.num_obs:], obs), dim=-1)
        return {'obs': obs, 'privileged_obs': privileged_obs, 'obs_history': self.obs_history}, rew, done, info

    def get_observations(self):
        obs = self.env.get_observations()
        privileged_obs = self.env.get_privileged_observations()
        # TODO: how to handle obs_history here?
        self.obs_history = torch.cat((self.obs_history[:, self.env.num_obs:], obs), dim=-1)
        return {'obs': obs, 'privileged_obs': privileged_obs, 'obs_history': self.obs_history}

    def get_obs(self):
        obs = self.env.get_obs()
        privileged_obs = self.env.get_privileged_observations()
        # TODO: how to handle obs_history here?
        self.obs_history = torch.cat((self.obs_history[:, self.env.num_obs:], obs), dim=-1)
        return {'obs': obs, 'privileged_obs': privileged_obs, 'obs_history': self.obs_history}

    def reset_idx(self, env_ids):  # it might be a problem that this isn't getting called!!
        ret = self.env.reset_idx(env_ids)
        self.obs_history[env_ids, :] = 0
        return ret

    def reset(self):
        ret = self.env.reset()
        privileged_obs = self.env.get_privileged_observations()
        self.obs_history[:, :] = 0
        return {"obs": ret, "privileged_obs": privileged_obs, "obs_history": self.obs_history}

    def __getattr__(self, name):
        return getattr(self.env, name)

if __name__ == "__main__":
    from tqdm import trange
    import matplotlib.pyplot as plt

    test_env = gym.make("legged_gym.envs:GapCrossingHardEnv-v0", randomize_motor_strength=True)
    env = RMAWrapper(test_env)

    env.reset()
    action = torch.zeros(test_env.num_envs, 12)
    for i in trange(3):
        obs, rew, done, info = env.step(action)
        print(obs.keys())
        print(f"obs: {obs['obs']}")
        print(f"privileged obs: {obs['privileged_obs']}")
        print(f"obs_history: {obs['obs_history']}")

        img = env.render('rgb_array')
        plt.imshow(img)
        plt.show()
