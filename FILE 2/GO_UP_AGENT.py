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
            nn.Dropout(0.2),  # Add dropout to prevent overfitting
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size//2),
            nn.ReLU(),
            nn.Linear(hidden_size//2, output_size)
        )

    def forward(self, x):
        return self.net(x)

class DQNAgent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 80
        self.gamma = 0.95  # Increased for longer-term planning
        self.memory = deque(maxlen=MAX_MEMORY)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.policy_net = DQNNetwork().to(self.device)
        self.target_net = DQNNetwork().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LR, weight_decay=1e-5)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, 'max', patience=10)

        self.record = 0
        self.total_score = 0
        self.mean_score = 0
        self.training_step = 0

    def remember(self, state, action, reward, next_state, done):
        # Store experience with movement info
        self.memory.append((state, action, reward, next_state, done))

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

        # Random sample from memory
        mini_sample = random.sample(self.memory, BATCH_SIZE)
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
        # Exploration vs exploitation
        self.epsilon = max(80 - self.n_games, 5)
        final_move = 0

        if random.randint(0, 200) < self.epsilon:
            final_move = random.randint(0, 3)
        else:
            state0 = torch.FloatTensor(state).to(self.device)
            prediction = self.policy_net(state0)
            final_move = torch.argmax(prediction).item()

        return final_move

    def update_scores(self, score):
        self.total_score += score
        self.mean_score = self.total_score / self.n_games
        if score > self.record:
            self.record = score