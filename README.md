# V.E.R.A. (Virtual Electronic Remote Assistant)
> **"Protocol: Online."**

![Build Status](https://github.com/NaeemBrown/VERA/actions/workflows/build.yml/badge.svg)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey)

**V.E.R.A.** is a locally-hosted, voice-activated AI Operating System designed for power users, developers, and IT professionals. Unlike standard assistants, V.E.R.A. has full control over the host machine—capable of writing code, debugging screens, managing windows, and executing complex workflows.

---

## 🧠 System Architecture
V.E.R.A. utilizes a **Dual-Core AI Approach**:
* **The Speed Brain (Groq / Llama 3):** Handles rapid conversation, command routing, and logic (Latency: <0.5s).
* **The Vision Brain (Google Gemini 2.0):** Handles image analysis, screen reading, and object identification.

## ⚡ Key Features

### 👁️ Computer Vision & Control
* **Hand Mouse Protocol:** Control the cursor with hand gestures (Minority Report style) using OpenCV & MediaPipe.
* **Screen Analysis:** Ask *"What is this error?"* and V.E.R.A. will screenshot your desktop and debug the log.
* **Object ID:** Show an object to the webcam, and she will identify it.

### 🛠️ Desktop Automation
* **App Management:** *"Open VS Code"*, *"Close Chrome"*, *"Kill process"*.
* **Window Snapping:** *"Snap Spotify right"*, *"Maximize this"*.
* **System Stats:** Real-time HUD overlay of CPU, RAM, and Battery levels.
* **Volume Control:** Smart fading audio (smooth transitions) or instant muting.

### 📂 Productivity
* **The Janitor:** Automatically sorts your `Downloads` folder into categories (Images, Docs, Installers).
* **Smart Notes:** Dictate notes that save directly to a local log file.
* **Clipboard Reader:** Reads copied text aloud.

---

## 🚀 Installation

### Prerequisites
* Windows 10/11
* Python 3.11 or higher
* A webcam (for Hand Mouse & Vision)

### Quick Start
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NaeemBrown/VERA.git
    cd VERA
    ```

2.  **Run the Installer:**
    Double-click `setup.bat`.
    *(This script automatically creates a virtual environment and installs all dependencies).*

3.  **Configure Keys:**
    Create a file named `.env` in the root folder and add your API keys:
    ```env
    GROQ_API_KEY=gsk_...
    GEMINI_API_KEY=AIzaSy...
    ```

4.  **Launch:**
    Double-click `run.bat` or run:
    ```bash
    python interface.py
    ```

---

## 🗣️ Command Reference

| Intent | Voice Command Examples |
| :--- | :--- |
| **Vision** | *"Activate mouse"*, *"Stop tracking"*, *"What am I holding?"*, *"Read this screen"* |
| **System** | *"System status"*, *"CPU level"*, *"Set volume to 50%"* |
| **Media** | *"Play [song name]"*, *"Next song"*, *"Pause music"* |
| **Apps** | *"Open Calculator"*, *"Close Discord"*, *"Snap left"* |
| **Utils** | *"Clean my downloads"*, *"Take a screenshot"*, *"Set a timer for 5 minutes"* |
| **Chat** | *"Explain quantum physics"*, *"Write a python script for..."* |

---

## 🛡️ Privacy & Security
* **Local Processing:** Voice activation and hand tracking run locally.
* **No Cloud Logs:** Screenshots taken for analysis are processed by the API and not stored on any external server.
* **API Security:** Keys are loaded via `.env` and excluded from version control.

---

## 🛠️ Engineering Standards
V.E.R.A. is built with a production-grade DevOps pipeline:
* **CI/CD Pipeline:** GitHub Actions automatically builds and tests every commit.
* **Static Analysis:** Code style is enforced via `Black` and Pre-Commit Hooks.
* **Integration Testing:** Critical modules are verified with `pytest` before deployment.
* **Artifact Delivery:** Successful builds automatically compile a portable `.exe`.

---

## 🔮 Roadmap (Upcoming Modules)
* [ ] **Intruder Alert:** Facial recognition scanner to alert user of foreign users at desktop.
* [ ] **Protocol: Ghost:** Instant privacy mode (minimize all + mute).
* [ ] **IoT Integration:** Smart light control (Yeelight/Hue).

---

**Author:** Naeem Brown
