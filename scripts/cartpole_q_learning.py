"""
    CartPole actions are modelled as binary 
    actions (left & right), and CartPole 
    has discrete action space. The 'epsilon' 
    value is used to balance 'Exploration' 
    vs 'Exploitation'"""

import gym
import argparse
import numpy as np
import matplotlib.pyplot as plt
from IPython import display as i_python_display

class MyEnvironment:
    def __init__(self, environment_name: str, action = None, observation = None) -> None:
        self.environment_name = environment_name
        self.environment = gym.make(self.environment_name)
        self.action = action
        self.observation = observation
        if 'CartPole' in self.environment_name:
            self.n_bins = 20
            self.bins = [np.linspace(-4.8, 4.8, self.n_bins), \
                np.linspace(-4, 4, self.n_bins), \
                    np.linspace(-0.418, 0.418, self.n_bins), \
                        np.linspace(-4, 4, self.n_bins)]


    def get_environment_name(self) -> str: 
        """Returns the name of the environment"""
        return self.environment.unwrapped.spec.id 

    def get_action_space(self):
        return self.environment.action_space

    def get_action_space_length(self):
        if 'CartPole' in self.environment_name:
            return 2
        return self.environment.action_space.n

    def get_observation_space(self):
        return self.environment.observation_space
    
    def get_observation_space_length(self):
        if 'CartPole' in self.environment_name:
            return [self.n_bins+1] \
                * len(self.environment.observation_space.high)
        return [self.environment.horizon + 1]

    def set_observation(self, observation) -> None:
        self.observation = observation
        if 'CartPole' in self.environment_name:
            # discretize the observation
            observation_index = []
            for i in range(len(self.get_observation_space().high)):
                observation_index.append(np.digitize(self.observation[i], \
                    self.bins[i]) - 1)  # subtract 1 to convert bin into index 
            self.observation = tuple(observation_index)

    def display_environment(self):
        plt.imshow(self.environment.render(mode = 'rgb_array'))

    def reset(self):
        return self.environment.reset()

    def step(self):
        return self.environment.step(self.action)

    def render(self):
        return self.environment.render()

    def close(self):
        self.environment.close()



class Agent:
    def __init__(self, action_space: gym.spaces.Discrete, action_space_length, \
        observation_space: gym.spaces.Discrete, observation_space_length, \
            n_episodes: int, learning_rate: float, gamma: float):
        
        self.action_space = action_space 
        self.action_space_length = action_space_length
        self.observation_space = observation_space
        self.observation_space_length = observation_space_length 
        self.n_episodes = n_episodes 
        self.epsilon = np.exp(-5 * np.linspace(0, 1, n_episodes)) 
        self.q_table = np.random.uniform(low = -2, high = 0, \
            size = (self.observation_space_length + [self.action_space_length]))
        self.learning_rate = learning_rate
        self.gamma = gamma 
    
    def act(self, observation: int, episode_number: int) -> int:
        """
            Returns an action based on 'epsilon 
            greedy condition,' i.e., returns a 
            uniformly sampled random action from 
            the action space if the random number 
            generated is less than epsilon, else, 
            the action that has the highest 
            Q-value in observation/ state"""

        if np.random.uniform(1.0, 0.0) < self.epsilon[episode_number]: 
            return self.action_space.sample()
        return np.argmax(self.q_table[observation]) 

    def update(self, observation: int, action: int, \
        next_observation: int, reward: float) -> float:
        """
            Estimates the optimal future Q-value
            i.e., the maximum Q-value in next
            observation, updates the Q-table and
            returns the change in Q-value"""

        q_value = self.q_table[observation][action]
        next_q_value_estimate = np.max(self.q_table[next_observation]) 
        temporal_difference_target = reward + self.gamma * next_q_value_estimate
        self.q_table[observation][action] \
            += self.learning_rate * (temporal_difference_target - q_value)
        return self.q_table[observation][action] - q_value



def plot_statistics(running_accuracy, running_delta):
    step_size = round(n_episodes/20)
    x = np.arange(1, n_episodes, step_size)
    markers = ["C8-","C20"]
    fig, (ax1, ax2) = plt.subplots(2, sharex = True)
    fig.suptitle('Performance vs Episode Number')
    ax1.plot(x, running_accuracy[1: -1: step_size], markers[0])
    ax1.set(ylabel = 'Accuracy')
    ax2.plot(x, running_delta[1: -1: step_size], markers[1])
    ax2.set(ylabel = 'Delta')
    plt.savefig('cartpole_q_learning.jpg')
    plt.show()



def main():
    
    np.random.seed(111989)
    
    # display once in every 100 episodes 
    DISPLAY_FREQUENCY = 100 

    # create and reset environment
    environment = MyEnvironment('CartPole-v1')
    environment.reset()

    # get inputs for agent from the environment
    action_space = environment.get_action_space()
    action_space_length = environment.get_action_space_length()
    observation_space = environment.get_observation_space()
    observation_space_length = environment.get_observation_space_length()

    # create agent
    agent = Agent(action_space, action_space_length, observation_space, \
        observation_space_length, n_episodes, learning_rate, gamma)

    # display the environment
    environment.display_environment()

    # initialize performance indicators
    running_length = 5 
    running_delta, running_accuracy = [], [] 
    render_gym = True
    for episode_index in range(n_episodes):
        """
            Track the number of episodes completed
            (episode_count), the number of actions 
            that yield maximum reward or successes
            (optimal_actions), cumulative reward 
            and delta update of the Q-table"""

        episode_count = 1 
        optimal_actions = 0  
        delta_update = [] 

        # get the initial observation 
        observation = environment.reset()
        environment.set_observation(observation)
        observation = environment.observation 

        done = False
        while not done:
            # display performance
            if episode_index % DISPLAY_FREQUENCY == 0:
                if render_gym and ('CartPole' in environment.environment_name):
                    environment.display_environment()
                    i_python_display.clear_output(wait = True)
                    i_python_display.display(plt.gcf())
                    
            action = agent.act(observation, episode_index) 
            environment.action = action
            next_observation, reward, done, _ = environment.step()
            environment.set_observation(next_observation)
            next_observation = environment.observation

            delta_update.append(agent.update(observation, action, \
                next_observation, reward)) 

            observation = next_observation 
            
            optimal_actions += int(reward > 0.0)
            episode_count += 1

        # compute performance statistics and display performance
        running_delta.append(sum(delta_update).item()) # latest update
        running_accuracy.append(optimal_actions/episode_count) # latest accuracy

        print('episode = {}, epsilon = {}, cumulative delta = {}, accuracy = {} \n'\
            .format(episode_index, agent.epsilon[episode_index], \
                running_delta[episode_index], running_accuracy[-1]))

        if (episode_index >= n_episodes + running_length ) or \
            (all([accuracy == 1.0 for accuracy in running_accuracy]) and \
                all([delta < 0.0001 for delta in running_delta]) and \
                    episode_index >= running_length): break

    i_python_display.clear_output(wait = True)
    environment.close() 

    # plot performance statistics
    plot_statistics(running_accuracy, running_delta)



if __name__ == "__main__":
    
    #parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', type = int, default = 10000, \
        help = 'Number of steps in epsilon log-space, or iterations')
    parser.add_argument('--alpha', type = float, default = 0.1, \
        help = 'Learning rate')
    parser.add_argument('--gamma', type = float, default = 0.95, \
        help = 'Gamma parameter')
    
    args = vars(parser.parse_args())
    n_episodes = int(args['episodes'])
    learning_rate = float(args['alpha'])
    gamma = float(args['gamma'])

    main()
