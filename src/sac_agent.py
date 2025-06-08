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
    def __init__(self, state_dim, action_dim, hidden_dim):
        super(CriticNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
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

    def forward(self, state, action):
        # state: (batch_size, state_dim), action: (batch_size, action_dim)
        x = torch.cat([state, action], dim=-1)
        return self.network(x)

class SACAgent:
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        # Flatten the state dimension
        flattened_state_dim = sum(np.prod(space.shape) for space in state_dim.values())
        self.actor = ActorNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.critic1 = CriticNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.critic2 = CriticNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.target_critic1 = CriticNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.target_critic2 = CriticNetwork(flattened_state_dim, action_dim, hidden_dim)
        self.target_critic1.load_state_dict(self.critic1.state_dict())
        self.target_critic2.load_state_dict(self.critic2.state_dict())
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=3e-4)
        self.critic1_optimizer = optim.Adam(self.critic1.parameters(), lr=3e-4)
        self.critic2_optimizer = optim.Adam(self.critic2.parameters(), lr=3e-4)
        self.alpha = 0.2
        self.gamma = 0.99
        self.tau = 0.005
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.actor.to(self.device)
        self.critic1.to(self.device)
        self.critic2.to(self.device)
        self.target_critic1.to(self.device)
        self.target_critic2.to(self.device)

    def select_action(self, state, evaluate=False):
        with torch.no_grad():
            # Flatten and convert state to tensor
            flattened_state = torch.cat([torch.tensor(state[key], dtype=torch.float32).flatten() for key in state.keys()])
            logger.debug(f"Flattened state: {flattened_state}")
            # Check for NaN/inf in state
            if torch.isnan(flattened_state).any() or torch.isinf(flattened_state).any():
                logger.error(f"NaN or Inf detected in flattened state: {flattened_state}")
                flattened_state = torch.nan_to_num(flattened_state, nan=0.0, posinf=0.0, neginf=0.0)
            mean, log_std = self.actor(flattened_state)
            logger.debug(f"Actor mean: {mean}, log_std: {log_std}")
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
            return action.cpu().numpy()
    
    def update(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Update networks using a batch of transitions."""
        # Convert batch to tensors
        state_dict = {k: torch.FloatTensor(v) for k, v in batch['state'].items()}
        next_state_dict = {k: torch.FloatTensor(v) for k, v in batch['next_state'].items()}
        action = torch.FloatTensor(batch['action'])
        reward = torch.FloatTensor(batch['reward'])
        done = torch.FloatTensor(batch['done'])

        # Scale rewards to be more meaningful
        reward = reward * 100  # Scale rewards to basis points

        # Flatten and concatenate state and next_state for each sample in the batch
        def flatten_state_dict(state_dict):
            # state_dict: {key: (batch_size, ...)}
            batch_size = list(state_dict.values())[0].shape[0]
            flat = []
            for i in range(batch_size):
                flat_i = torch.cat([
                    state_dict[k][i].flatten() for k in state_dict.keys()
                ])
                flat.append(flat_i)
            return torch.stack(flat)

        state = flatten_state_dict(state_dict)
        next_state = flatten_state_dict(next_state_dict)

        # Update critics
        with torch.no_grad():
            next_mean, next_log_std = self.actor(next_state)
            next_std = next_log_std.exp()
            next_action = next_mean + next_std * torch.randn_like(next_mean)
            next_action = torch.tanh(next_action)

            target_q1 = self.target_critic1(next_state, next_action)
            target_q2 = self.target_critic2(next_state, next_action)
            target_q = torch.min(target_q1, target_q2)
            target_q = reward.unsqueeze(1) + (1 - done.unsqueeze(1)) * self.gamma * target_q

        current_q1 = self.critic1(state, action)
        current_q2 = self.critic2(state, action)

        critic1_loss = F.mse_loss(current_q1, target_q)
        critic2_loss = F.mse_loss(current_q2, target_q)

        self.critic1_optimizer.zero_grad()
        critic1_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic1.parameters(), max_norm=1.0)
        self.critic1_optimizer.step()

        self.critic2_optimizer.zero_grad()
        critic2_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic2.parameters(), max_norm=1.0)
        self.critic2_optimizer.step()

        # Update actor
        mean, log_std = self.actor(state)
        std = log_std.exp()
        action = mean + std * torch.randn_like(mean)
        action = torch.tanh(action)

        q1 = self.critic1(state, action)
        q2 = self.critic2(state, action)
        q = torch.min(q1, q2)

        # Calculate policy entropy
        # For a Gaussian distribution, entropy = 0.5 * (log(2*pi) + 1 + 2*log(std))
        policy_entropy = 0.5 * (np.log(2 * np.pi) + 1 + 2 * log_std).mean()

        actor_loss = (self.alpha * log_std + log_std.exp() - q).mean()

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=1.0)
        self.actor_optimizer.step()

        # Update target networks
        for param, target_param in zip(self.critic1.parameters(), self.target_critic1.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

        for param, target_param in zip(self.critic2.parameters(), self.target_critic2.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

        return {
            'actor_loss': actor_loss.item(),
            'critic1_loss': critic1_loss.item(),
            'critic2_loss': critic2_loss.item(),
            'policy_entropy': policy_entropy.item()
        }

    def save(self, path: str):
        """Save the SAC model state."""
        state_dict = {
            'actor': self.actor.state_dict(),
            'critic1': self.critic1.state_dict(),
            'critic2': self.critic2.state_dict(),
            'target_critic1': self.target_critic1.state_dict(),
            'target_critic2': self.target_critic2.state_dict(),
            'actor_optimizer': self.actor_optimizer.state_dict(),
            'critic1_optimizer': self.critic1_optimizer.state_dict(),
            'critic2_optimizer': self.critic2_optimizer.state_dict(),
            'alpha': self.alpha,
            'gamma': self.gamma,
            'tau': self.tau
        }
        torch.save(state_dict, path)
        logger.info(f"SAC model saved to {path}")
        
    def load(self, path: str):
        """Load the SAC model state."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")
            
        state_dict = torch.load(path, map_location=self.device)
        
        # Load network states
        self.actor.load_state_dict(state_dict['actor'])
        self.critic1.load_state_dict(state_dict['critic1'])
        self.critic2.load_state_dict(state_dict['critic2'])
        self.target_critic1.load_state_dict(state_dict['target_critic1'])
        self.target_critic2.load_state_dict(state_dict['target_critic2'])
        
        # Load optimizer states
        self.actor_optimizer.load_state_dict(state_dict['actor_optimizer'])
        self.critic1_optimizer.load_state_dict(state_dict['critic1_optimizer'])
        self.critic2_optimizer.load_state_dict(state_dict['critic2_optimizer'])
        
        # Load hyperparameters
        self.alpha = state_dict['alpha']
        self.gamma = state_dict['gamma']
        self.tau = state_dict['tau']
        
        logger.info(f"SAC model loaded from {path}") 