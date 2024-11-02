import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random
import pygame

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class DQNNetwork(nn.Module):
    def __init__(self, input_size=16, hidden_size=256, output_size=4):  # Updated input_size
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.LayerNorm(hidden_size),  # Add normalization
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, hidden_size//2),
            nn.ReLU(),
            nn.Linear(hidden_size//2, output_size)
        )
    
    def forward(self, x):
        return self.net(x)
    
class DQNAgent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 100
        self.gamma = 0.98  # Increased for longer-term planning
        self.memory = deque(maxlen=MAX_MEMORY)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.min_epsilon = 10  # Higher minimum exploration
        self.epsilon_decay = 0.995
        
        self.policy_net = DQNNetwork().to(self.device)
        self.target_net = DQNNetwork().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LR, weight_decay=1e-5)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, 'max', patience=10)
        
        self.record = 0
        self.total_score = 0
        self.mean_score = 0
        self.training_step = 0
        self.last_action = None
        self.consecutive_actions = 0
        self.max_consecutive = 3
        self.memory = deque(maxlen=MAX_MEMORY)
        self.priority_memory = deque(maxlen=1000)
        # Add platform tracking
        self.last_platform = None
        self.platform_visits = {}

    def remember(self, state, action, reward, next_state, done):
        # Store experience with movement info
        self.memory.append((state, action, reward, next_state, done))
        if reward > 10:  # Significant positive reward
            self.priority_memory.append((state, action, reward, next_state, done))

    def train_short_memory(self, state, action, reward, next_state, done):
        """Train immediately on the latest action"""
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        next_state = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
        action = torch.LongTensor([action]).to(self.device)
        reward = torch.FloatTensor([reward]).to(self.device)
        done = torch.BoolTensor([done]).to(self.device)

        # Current Q values
        current_q = self.policy_net(state)
        # Next Q values from target net
        with torch.no_grad():
            next_q = self.target_net(next_state)
            max_next_q = next_q.max(1)[0].unsqueeze(1)
            target_q = reward + (1 - done.float()) * self.gamma * max_next_q

        # Update specific action
        current_q_action = current_q.gather(1, action.unsqueeze(1))
        loss = nn.MSELoss()(current_q_action, target_q)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def train_long_memory(self):
        """Learn from batch of experiences after episode"""
        if len(self.memory) < BATCH_SIZE:
            return
        
        regular_size = BATCH_SIZE // 2
        priority_size = BATCH_SIZE - regular_size
        
        regular_sample = random.sample(self.memory, regular_size)
        priority_sample = random.sample(self.priority_memory, min(priority_size, len(self.priority_memory)))
        mini_sample = regular_sample + priority_sample

        states, actions, rewards, next_states, dones = zip(*mini_sample)

        # Convert to tensors
        states = torch.FloatTensor(np.array(states)).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        actions = torch.LongTensor(np.array(actions)).to(self.device)
        rewards = torch.FloatTensor(np.array(rewards)).to(self.device)
        dones = torch.BoolTensor(np.array(dones)).to(self.device)

        # Current Q values
        current_q = self.policy_net(states)
        current_q_actions = current_q.gather(1, actions.unsqueeze(1))

        # Next Q values from target net
        with torch.no_grad():
            next_q = self.target_net(next_states)
            max_next_q = next_q.max(1)[0].unsqueeze(1)
            target_q = rewards.unsqueeze(1) + (1 - dones.float().unsqueeze(1)) * self.gamma * max_next_q

        # Compute loss and optimize
        loss = nn.MSELoss()(current_q_actions, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update target network periodically
        if self.n_games % 5 == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

    def act(self, state):
        state = torch.FloatTensor(state).reshape(1, -1).to(self.device)  # Reshape to (1, 16)

        self.epsilon = max(
            self.min_epsilon,
            100 * (0.995 ** self.n_games)  # Smoother decay
        )
        if random.randint(0, 200) < self.epsilon:
            # Avoid repeating same action too many times during exploration
            if self.last_action is not None and self.consecutive_actions >= self.max_consecutive:
                actions = [0,1,2,3]
                actions.remove(self.last_action)
                final_move = random.choice(actions)
            else:
                final_move = random.randint(0, 3)
        else:
            state0 = torch.FloatTensor(state).to(self.device)
            prediction = self.policy_net(state0)
            final_move = torch.argmax(prediction).item()
        
        # Track consecutive actions
        if final_move == self.last_action:
            self.consecutive_actions += 1
        else:
            self.consecutive_actions = 0
        self.last_action = final_move
            
        return final_move
    
    def update_scores(self, score):
        self.total_score += score
        self.mean_score = self.total_score / self.n_games
        if score > self.record:
            self.record = score