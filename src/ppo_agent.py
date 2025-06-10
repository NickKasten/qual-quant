import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, List
import logging
import torch.optim as optim
import os

logger = logging.getLogger(__name__)

class ActorNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim):
        super(ActorNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.mean = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Linear(hidden_dim, action_dim)
        
        # Initialize weights
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0.0)

    def forward(self, state):
        features = self.network(state)
        mean = self.mean(features)
        log_std = self.log_std(features)
        log_std = torch.clamp(log_std, -20, 2)  # Prevent too small or large std
        return mean, log_std

class CriticNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim):
        super(CriticNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        # Initialize weights with orthogonal initialization
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)

    def forward(self, state):
        return self.network(state)

class PPOMemory:
    def __init__(self, batch_size):
        self.states = []
        self.actions = []
        self.probs = []
        self.vals = []
        self.rewards = []
        self.dones = []
        self.batch_size = batch_size

    def generate_batches(self):
        n_states = len(self.states)
        batch_start = np.arange(0, n_states, self.batch_size)
        indices = np.arange(n_states, dtype=np.int64)
        np.random.shuffle(indices)
        batches = [indices[i:i+self.batch_size] for i in batch_start]

        return np.array(self.states), np.array(self.actions), \
               np.array(self.probs), np.array(self.vals), \
               np.array(self.rewards), np.array(self.dones), batches

    def store_memory(self, state, action, probs, vals, reward, done):
        self.states.append(state)
        self.actions.append(action)
        self.probs.append(probs)
        self.vals.append(vals)
        self.rewards.append(reward)
        self.dones.append(done)

    def clear_memory(self):
        self.states = []
        self.actions = []
        self.probs = []
        self.vals = []
        self.rewards = []
        self.dones = []

class PPOAgent:
    def __init__(self, state_dim, action_dim, hidden_dim=256, learning_rate=3e-4, gamma=0.99, gae_lambda=0.95, epsilon=0.2):
        # Flatten the state dimension
        flattened_state_dim = sum(np.prod(space.shape) for space in state_dim.values())
        
        self.actor = ActorNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.critic = CriticNetwork(flattened_state_dim, hidden_dim)
        
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=learning_rate)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=learning_rate)
        
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.epsilon = epsilon
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.actor.to(self.device)
        self.critic.to(self.device)

    def select_action(self, state, evaluate=False):
        with torch.no_grad():
            # Flatten and convert state to tensor
            flattened_state = torch.cat([torch.tensor(state[key], dtype=torch.float32).flatten() for key in state.keys()])
            
            # Check for NaN/inf in state
            if torch.isnan(flattened_state).any() or torch.isinf(flattened_state).any():
                logger.error(f"NaN or Inf detected in flattened state: {flattened_state}")
                flattened_state = torch.nan_to_num(flattened_state, nan=0.0, posinf=0.0, neginf=0.0)
                
            mean, log_std = self.actor(flattened_state)
            
            # Check for NaN/inf in actor output
            if torch.isnan(mean).any() or torch.isinf(mean).any() or torch.isnan(log_std).any() or torch.isinf(log_std).any():
                logger.error(f"NaN or Inf detected in actor output. State: {flattened_state}, Mean: {mean}, Log Std: {log_std}")
                mean = torch.nan_to_num(mean, nan=0.0, posinf=0.0, neginf=0.0)
                log_std = torch.nan_to_num(log_std, nan=0.0, posinf=0.0, neginf=0.0)
                
            if evaluate:
                return mean.cpu().numpy()
                
            std = log_std.exp()
            # Check for NaN/inf in std
            if torch.isnan(std).any() or torch.isinf(std).any():
                logger.error(f"NaN or Inf detected in std. State: {flattened_state}, Mean: {mean}, Log Std: {log_std}, Std: {std}")
                std = torch.nan_to_num(std, nan=1.0, posinf=1.0, neginf=1.0)
                
            normal = torch.distributions.Normal(mean, std)
            x_t = normal.rsample()
            action = torch.tanh(x_t)
            
            # Calculate log probability
            log_prob = normal.log_prob(x_t)
            log_prob -= torch.log(1 - action.pow(2) + 1e-6)
            log_prob = log_prob.sum(-1, keepdim=True)
            
            return action.cpu().numpy(), log_prob.cpu().numpy()

    def compute_gae(self, rewards, values, dones, next_value):
        advantages = np.zeros_like(rewards)
        last_gae_lam = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value_t = next_value
            else:
                next_value_t = values[t + 1]
                
            delta = rewards[t] + self.gamma * next_value_t * (1 - dones[t]) - values[t]
            last_gae_lam = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_gae_lam
            advantages[t] = last_gae_lam
            
        returns = advantages + values
        return advantages, returns

    def update(self, memory: PPOMemory) -> Dict[str, float]:
        """Update networks using stored memory."""
        states, actions, old_probs, values, rewards, dones, batches = memory.generate_batches()
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.FloatTensor(actions).to(self.device)
        old_probs = torch.FloatTensor(old_probs).to(self.device)
        values = torch.FloatTensor(values).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Scale rewards to be more meaningful
        rewards = rewards * 100  # Scale rewards to basis points
        
        # Compute GAE
        advantages, returns = self.compute_gae(rewards.cpu().numpy(), 
                                            values.cpu().numpy(), 
                                            dones.cpu().numpy(), 
                                            0)  # next_value is 0 for terminal state
        
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        total_actor_loss = 0
        total_critic_loss = 0
        
        for batch in batches:
            # Get batch data
            batch_states = states[batch]
            batch_actions = actions[batch]
            batch_old_probs = old_probs[batch]
            batch_advantages = advantages[batch]
            batch_returns = returns[batch]
            
            # Update critic
            self.critic_optimizer.zero_grad()
            value_pred = self.critic(batch_states)
            critic_loss = F.mse_loss(value_pred, batch_returns)
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(), max_norm=0.5)
            self.critic_optimizer.step()
            
            # Update actor
            self.actor_optimizer.zero_grad()
            mean, log_std = self.actor(batch_states)
            std = log_std.exp()
            normal = torch.distributions.Normal(mean, std)
            new_probs = normal.log_prob(batch_actions)
            new_probs -= torch.log(1 - batch_actions.pow(2) + 1e-6)
            new_probs = new_probs.sum(-1, keepdim=True)
            
            ratio = torch.exp(new_probs - batch_old_probs)
            surr1 = ratio * batch_advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * batch_advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=0.5)
            self.actor_optimizer.step()
            
            total_actor_loss += actor_loss.item()
            total_critic_loss += critic_loss.item()
        
        return {
            'actor_loss': total_actor_loss / len(batches),
            'critic_loss': total_critic_loss / len(batches)
        }

    def save(self, path: str):
        """Save the PPO model state."""
        state_dict = {
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict(),
            'actor_optimizer': self.actor_optimizer.state_dict(),
            'critic_optimizer': self.critic_optimizer.state_dict(),
            'gamma': self.gamma,
            'gae_lambda': self.gae_lambda,
            'epsilon': self.epsilon
        }
        torch.save(state_dict, path)
        logger.info(f"PPO model saved to {path}")
        
    def load(self, path: str):
        """Load the PPO model state."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")
            
        state_dict = torch.load(path, map_location=self.device)
        
        # Load network states
        self.actor.load_state_dict(state_dict['actor'])
        self.critic.load_state_dict(state_dict['critic'])
        
        # Load optimizer states
        self.actor_optimizer.load_state_dict(state_dict['actor_optimizer'])
        self.critic_optimizer.load_state_dict(state_dict['critic_optimizer'])
        
        # Load hyperparameters
        self.gamma = state_dict['gamma']
        self.gae_lambda = state_dict['gae_lambda']
        self.epsilon = state_dict['epsilon']
        
        logger.info(f"PPO model loaded from {path}") 