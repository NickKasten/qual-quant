import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)

class ActorNetwork(nn.Module):
    def __init__(self, state_dim: Dict[str, Tuple[int, ...]], action_dim: int, hidden_dim: int = 256):
        super(ActorNetwork, self).__init__()
        
        # Market data encoder
        self.market_encoder = nn.Sequential(
            nn.Linear(state_dim['market_data'][0] * state_dim['market_data'][1], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Technical indicators encoder
        self.technical_encoder = nn.Sequential(
            nn.Linear(state_dim['technical_indicators'][0] * state_dim['technical_indicators'][1], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Portfolio state encoder
        self.portfolio_encoder = nn.Sequential(
            nn.Linear(state_dim['portfolio_state'][0], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Combined layers
        self.combined = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Output layers for mean and log_std
        self.mean = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, state: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        # Process each component of the state
        market_flat = state['market_data'].view(state['market_data'].shape[0], -1)
        technical_flat = state['technical_indicators'].view(state['technical_indicators'].shape[0], -1)
        
        market_features = self.market_encoder(market_flat)
        technical_features = self.technical_encoder(technical_flat)
        portfolio_features = self.portfolio_encoder(state['portfolio_state'])
        
        # Combine features
        combined = torch.cat([market_features, technical_features, portfolio_features], dim=1)
        features = self.combined(combined)
        
        # Get mean and log_std
        mean = self.mean(features)
        log_std = self.log_std(features)
        log_std = torch.clamp(log_std, -20, 2)  # Prevent too small or large std
        
        return mean, log_std

class CriticNetwork(nn.Module):
    def __init__(self, state_dim: Dict[str, Tuple[int, ...]], action_dim: int, hidden_dim: int = 256):
        super(CriticNetwork, self).__init__()
        
        # State encoders (same as actor)
        self.market_encoder = nn.Sequential(
            nn.Linear(state_dim['market_data'][0] * state_dim['market_data'][1], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.technical_encoder = nn.Sequential(
            nn.Linear(state_dim['technical_indicators'][0] * state_dim['technical_indicators'][1], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.portfolio_encoder = nn.Sequential(
            nn.Linear(state_dim['portfolio_state'][0], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Action encoder
        self.action_encoder = nn.Sequential(
            nn.Linear(action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Combined layers
        self.combined = nn.Sequential(
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, state: Dict[str, torch.Tensor], action: torch.Tensor) -> torch.Tensor:
        # Process state components
        market_flat = state['market_data'].view(state['market_data'].shape[0], -1)
        technical_flat = state['technical_indicators'].view(state['technical_indicators'].shape[0], -1)
        
        market_features = self.market_encoder(market_flat)
        technical_features = self.technical_encoder(technical_flat)
        portfolio_features = self.portfolio_encoder(state['portfolio_state'])
        action_features = self.action_encoder(action)
        
        # Combine all features
        combined = torch.cat([market_features, technical_features, portfolio_features, action_features], dim=1)
        q_value = self.combined(combined)
        
        return q_value

class SACAgent:
    def __init__(self, state_dim: Dict[str, Tuple[int, ...]], action_dim: int, 
                 hidden_dim: int = 256, lr: float = 3e-4, gamma: float = 0.99,
                 tau: float = 0.005, alpha: float = 0.2):
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha
        
        # Initialize networks
        self.actor = ActorNetwork(state_dim, action_dim, hidden_dim)
        self.critic1 = CriticNetwork(state_dim, action_dim, hidden_dim)
        self.critic2 = CriticNetwork(state_dim, action_dim, hidden_dim)
        self.target_critic1 = CriticNetwork(state_dim, action_dim, hidden_dim)
        self.target_critic2 = CriticNetwork(state_dim, action_dim, hidden_dim)
        
        # Initialize target networks
        self.target_critic1.load_state_dict(self.critic1.state_dict())
        self.target_critic2.load_state_dict(self.critic2.state_dict())
        
        # Initialize optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr)
        self.critic1_optimizer = torch.optim.Adam(self.critic1.parameters(), lr=lr)
        self.critic2_optimizer = torch.optim.Adam(self.critic2.parameters(), lr=lr)
        
    def select_action(self, state: Dict[str, torch.Tensor], evaluate: bool = False) -> np.ndarray:
        """Select action using the actor network."""
        with torch.no_grad():
            mean, log_std = self.actor(state)
            std = log_std.exp()
            
            if evaluate:
                action = mean
            else:
                action = mean + std * torch.randn_like(mean)
                
            action = torch.tanh(action)  # Bound actions to [-1, 1]
            
        return action.cpu().numpy()
    
    def update(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Update networks using a batch of transitions."""
        # Convert batch to tensors
        state = {k: torch.FloatTensor(v) for k, v in batch['state'].items()}
        action = torch.FloatTensor(batch['action'])
        reward = torch.FloatTensor(batch['reward'])
        next_state = {k: torch.FloatTensor(v) for k, v in batch['next_state'].items()}
        done = torch.FloatTensor(batch['done'])
        
        # Update critics
        with torch.no_grad():
            next_mean, next_log_std = self.actor(next_state)
            next_std = next_log_std.exp()
            next_action = next_mean + next_std * torch.randn_like(next_mean)
            next_action = torch.tanh(next_action)
            
            target_q1 = self.target_critic1(next_state, next_action)
            target_q2 = self.target_critic2(next_state, next_action)
            target_q = torch.min(target_q1, target_q2)
            target_q = reward + (1 - done) * self.gamma * target_q
            
        current_q1 = self.critic1(state, action)
        current_q2 = self.critic2(state, action)
        
        critic1_loss = F.mse_loss(current_q1, target_q)
        critic2_loss = F.mse_loss(current_q2, target_q)
        
        self.critic1_optimizer.zero_grad()
        critic1_loss.backward()
        self.critic1_optimizer.step()
        
        self.critic2_optimizer.zero_grad()
        critic2_loss.backward()
        self.critic2_optimizer.step()
        
        # Update actor
        mean, log_std = self.actor(state)
        std = log_std.exp()
        action = mean + std * torch.randn_like(mean)
        action = torch.tanh(action)
        
        q1 = self.critic1(state, action)
        q2 = self.critic2(state, action)
        q = torch.min(q1, q2)
        
        actor_loss = (self.alpha * log_std + log_std.exp() - q).mean()
        
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()
        
        # Update target networks
        for param, target_param in zip(self.critic1.parameters(), self.target_critic1.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            
        for param, target_param in zip(self.critic2.parameters(), self.target_critic2.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            
        return {
            'actor_loss': actor_loss.item(),
            'critic1_loss': critic1_loss.item(),
            'critic2_loss': critic2_loss.item()
        } 