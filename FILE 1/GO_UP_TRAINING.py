import pygame
import torch
from GO_Up_Ai import GoUpEnvironment
from GO_UP_AI_AGENT import DQNAgent
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def initialize_pygame():
    pygame.init()
    try:
        pygame.display.set_mode((1650, 950))  # Adjust size as needed
        return True
    except pygame.error:
        return False

# ... rest of your existing code ...

def train():
    running = True
    try:
        if not initialize_pygame():
            raise Exception("Failed to initialize Pygame display")
        
        env = GoUpEnvironment()
        agent = DQNAgent()
        
        episodes = 2000  # Increased episodes
        rewards_history = []
        best_reward = float('-inf')
        no_improvement_count = 0
        
        episode = 0
        while running and episode < episodes:
            try:
                state = env.reset()
                total_reward = 0
                done = False
                steps = 0
                
                # Episode loop
                while not done and steps < 10000 and running:
                    steps += 1
                    
                    # Get action
                    action = agent.act(state)
                    next_state, reward, done, _ = env.step(action)
                    
                    # Immediate feedback
                    agent.train_short_memory(state, action, reward, next_state, done)
                    agent.remember(state, action, reward, next_state, done)
                    
                    state = next_state
                    total_reward += reward
                    
                    # Handle events
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                
                if running:
                    # Episode completion
                    agent.train_long_memory()
                    agent.n_games += 1
                    rewards_history.append(total_reward)
                    
                    # Update learning rate based on performance
                    agent.scheduler.step(total_reward)
                    
                    # Track progress
                    mean_reward = np.mean(rewards_history[-100:]) if rewards_history else 0
                    
                    print(f"Episode: {episode + 1}/{episodes}, Steps: {steps}, "
                          f"Score: {total_reward:.2f}, Mean(100): {mean_reward:.2f}, "
                          f"Epsilon: {agent.epsilon:.3f}, Best: {best_reward:.2f}")
                    
                    # Save best model
                    if total_reward > best_reward:
                        best_reward = total_reward
                        no_improvement_count = 0
                        torch.save({
                            'episode': episode,
                            'model_state_dict': agent.policy_net.state_dict(),
                            'optimizer_state_dict': agent.optimizer.state_dict(),
                            'best_reward': best_reward,
                            'rewards_history': rewards_history,
                        }, 'best_model.pth')
                    else:
                        no_improvement_count += 1
                    
                    # Early stopping if no improvement
                    if no_improvement_count >= 200:
                        print("No improvement for 200 episodes. Stopping training.")
                        break
                    
                episode += 1
                
            except Exception as e:
                print(f"Error in episode {episode}: {e}")
                continue
                
    finally:
        # Cleanup and save final plots
        if len(rewards_history) > 0:
            plt.figure(figsize=(10, 5))
            plt.plot(rewards_history)
            plt.plot(np.convolve(rewards_history, np.ones(100)/100, mode='valid'))
            plt.title('Training Progress')
            plt.xlabel('Episode')
            plt.ylabel('Reward')
            plt.savefig(f'training_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            plt.close()

if __name__ == "__main__":
    train()