from rl_drone import RLAgent
from drone_sim_env import drone_sim

env = drone_sim()
agent = RLAgent(env)
ENV_NAME = 'drone'

agent.agent.fit(env, nb_steps=100000, visualize=True, verbose=1, nb_max_episode_steps=10)
agent.agent.save_weights('ddpg_{}_weights.h5f'.format(ENV_NAME), overwrite=True)
