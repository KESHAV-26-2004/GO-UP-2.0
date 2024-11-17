import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque
from GO_UP_TRAINING import Linear_QNet, Qtrainer
from GO_Up_Ai import GoUpEnvironment
import random
import os
from helper import plot
MAX_MEMORY = 200_000
BATCH_SIZE = 1000
LR = 0.001

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class Agent:
    def __init__(self):
        self.n_games = 0
        self.memory = deque(maxlen=MAX_MEMORY)
        self.epsilon = 0
        self.gamma = 0.98# Increased for longer-term planning
        self.model = Linear_QNet(11, 128, 3).to(device)
        self.trainer = Qtrainer(self.model, lr=LR, gamma=self.gamma)

    def remember(self, state, action, reward, next_state, done):
        # Store experience with movement info
        self.memory.append((state, action, reward, next_state, done))

    def train_short_memory(self, state, action, reward, next_state, done):
        state = torch.tensor(state, dtype=torch.float).to(device)
        next_state = torch.tensor(next_state, dtype=torch.float).to(device)
        action = torch.tensor(action, dtype=torch.long).to(device)
        reward = torch.tensor(reward, dtype=torch.float).to(device)
        done = torch.tensor(done, dtype=torch.bool).to(device)
        self.trainer.train_step(state, action, reward, next_state, done)

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)  

# Assuming `model` is your neural network and `optimizer` is your optimizer
    def save_checkpoint(agent, filename="model_checkpoint.pth"):
        checkpoint = {
            'model_state_dict': agent.model.state_dict(),
            'optimizer_state_dict': agent.trainer.optimizer.state_dict()
        }
        torch.save(checkpoint, filename)
        print(f"Model checkpoint saved to {filename}")

    def load_checkpoint(self, filename="model_checkpoint.pth"):
        checkpoint = torch.load(filename)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"Model checkpoint loaded from {filename}")

    '''def preprocess_state(self, state):
        """Preprocess the state data to make it more meaningful for the model"""
        # Assuming state contains player position and block positions
        
        # 1. Normalize positions to be relative to player
        player_x, player_y = state[0], state[1]
        blocks = state[2:]  # Rest of the state contains block positions
        
        # 2. Calculate relative positions and distances
        processed_state = []
        
        # Add normalized player position (0-1 range)
        processed_state.extend([
            player_x / GAME_WIDTH,
            player_y / GAME_HEIGHT
        ])
        
        # Process nearest blocks (assuming blocks come in pairs of x,y coordinates)
        nearest_blocks = []
        for i in range(0, len(blocks), 2):
            if i+1 < len(blocks):
                block_x, block_y = blocks[i], blocks[i+1]
                
                # Calculate relative positions
                rel_x = (block_x - player_x) / GAME_WIDTH
                rel_y = (block_y - player_y) / GAME_HEIGHT
                
                # Calculate distance
                distance = ((rel_x ** 2) + (rel_y ** 2)) ** 0.5
                
                nearest_blocks.append((rel_x, rel_y, distance))
        
        # Sort blocks by distance and take closest 2
        nearest_blocks.sort(key=lambda x: x[2])
        nearest_blocks = nearest_blocks[:2]
        
        # Add relative positions of nearest blocks
        for block in nearest_blocks:
            processed_state.extend([block[0], block[1]])  # Add relative x,y
            processed_state.append(block[2])              # Add distance
        
        return processed_state'''
    
    def act(self, state):
        # random moves: tradeoff exploration / exploitation
        #self.epsilon = 80 - self.n_games
        final_move = [0,0,0]
        self.epsilon = max(3, 90 - self.n_games * 0.5)

        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float).to(device)
            prediction = self.model(state0)
            #move = torch.argmax(prediction).item()
            move = (prediction + torch.randn_like(prediction) * 0.1).argmax().item()

            final_move[move] = 1

        return final_move
    
    def update_scores(self, score):
        self.total_score += score
        self.mean_score = self.total_score / self.n_games
        if score > self.record:
            self.record = score

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game_up = GoUpEnvironment()
    # Load checkpoint if needed
    #if(agent.n_games>0):
    #    agent.load_checkpoint()
    while True:
        # get old state
        state_old = game_up._get_state()

        # get move
        final_move = agent.act(state_old)

        # perform move and get new state
        reward, done, score = game_up.step(final_move)

        state_new = game_up._get_state()

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game_up.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if agent.n_games % 100 == 0:
                agent.save_checkpoint()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()