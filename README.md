# 🎮 GO UP 2.0 — AI-Enhanced Platformer Game

**GO UP 2.0** is a vertical-scrolling platformer game originally developed using **Pygame**.
In this version, we've implemented an **AI agent** trained to play the game using
**reinforcement learning techniques**. This project demonstrates a custom-built game
environment and the integration of AI for gameplay automation.

> 🚧 Status: AI model is currently under improvement — it shows continuous left-right
movement loops and is still being fine-tuned.

---

## 🧠 Project Highlights

- 🕹️ Original game mechanics and assets built in Python with Pygame
- 🧠 AI agent trained using Q-learning-like strategy
- 🎯 AI goal: Learn to jump on platforms, avoid falling, and reach higher scores
- 📦 Modular code structure: Game + Agent + Training separated cleanly
- 🔄 Two versions included — for comparison and progress tracking

---

## 📁 Repository Structure
```bash
GO_UP_AI/
├── FINAL/
│ ├── agent.py # Final agent code (run this)
│ ├── game.py # Final game logic with AI hooks
│ ├── model.pth # Trained agent model
│ └── utils.py # Helper functions
│
├── OLD_NO_AI(File 2)/
│ ├── game.py # Initial version of game without AI (6 months ago)
│ └── player.py # Manual player control logic
│
├── TRAINING (File 1)/
│ ├── train_agent.py # AI training script
│ ├── env.py # Game environment abstraction
│ └── rewards.py # Custom reward functions
│
└── README.md
```

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- VS Code (recommended)
- Install dependencies:
```bash
pip install pygame torch numpy
```
## ⚠️ Known Issues

🔁 AI sometimes loops left-right indefinitely — this behavior is due to reward structure bias or missing vertical progression rewards.

🎯 Currently working on:

Better jump detection

Reward optimization

Smoother movement control

## 💬 Notes

This project is fully custom — game and AI logic made from scratch

Uses basic RL principles (state > action > reward > next state)

Not based on OpenAI Gym — it's a self-built environment

## 📎 Download Instructions

📦 Download ZIP of full project

📁 Open it in VS Code

▶️ Run from the FINAL folder using python agent.py

---

👨‍💻 Developed By

Keshav
Bennett University | BTech CSE

---

## 🧾 Credits & Inspiration

This project was developed entirely by **Keshav**, but certain AI agent structuring concepts and reinforcement learning principles were inspired by:

- [freeCodeCamp.org - Snake AI with PyTorch](https://www.youtube.com/watch?v=FfWpgLFMI7w)
- [Patrick Loeber's Snake AI GitHub Repo](https://github.com/patrickloeber/snake-ai-pytorch)

---

📜 License

This project is built entirely from scratch for educational and research use.

You may fork or learn from it
