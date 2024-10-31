

# AIRIS Client - User Guide

This guide provides step-by-step instructions for setting up and running the AIRIS Client, a Minecraft-based AI tool. Follow the instructions for either **Windows** or **Linux** based on your operating system.

## Table of Contents
- [Requirements](#requirements)
- [Minecraft Setup](#minecraft-setup)
- [AIRIS Client Setup](#airis-client-setup)
  - [Windows Instructions](#windows-instructions)
  - [Linux Instructions](#linux-instructions)
- [Important Notes](#important-notes)

---

## Requirements

1. **Minecraft**: Ensure Minecraft Fabric version 1.20.1 is installed.
2. **Python 3.10**: Download from [Python Downloads](https://www.python.org/downloads/release/python-31011/).
3. **CurseForge**: Install from [CurseForge](https://www.curseforge.com/).

## Minecraft Setup

Launch CurseForge, search and install for:
   - **Vereya Mod** (required)
   - **Fabric API**


---

## AIRIS Client Setup

### Windows Instructions

1. **Open Terminal in the Repository Folder**: Navigate to the AIRIS Client folder in a terminal.
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the Virtual Environment**:
   ```bash
   .\venv\Scripts\activate
   ```
4. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. **Prepare Minecraft**: Launch Minecraft and create a single-player game with cheats enabled.
6. **Run AIRIS Client**:
   ```bash
   python minecraft_client.py --agent agent1qt05zd2vflz4vrytdyr2agz2775gv9e5hz99h06tq4uz6lv8fzq3k2dumzs
   ```

#### Visualization Tool for Windows

1. **Download the Visualization Tool**: [AIRIS Visual Tool](https://drive.google.com/file/d/1Th4T-ZFph-bJYlxVe1ZQA8MTl9X9YAmf/view?usp=sharing)
2. **Extract Files**: Unzip into the AIRIS client directory.
3. **Run Visualization**: After starting the AIRIS client, open `main.exe` in the client folder.
4. **Navigate**: Use your mouse and keyboard to adjust the view if the AIRIS agent isn’t immediately visible.

---

### Linux Instructions

1. **Open Terminal in the Repository Folder**.
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Prepare Minecraft**: Launch Minecraft and create a single-player game with cheats enabled.
6. **Run AIRIS Client**:
   ```bash
   python minecraft_client.py --agent agent1qt05zd2vflz4vrytdyr2agz2775gv9e5hz99h06tq4uz6lv8fzq3k2dumzs
   ```

#### Visualization Tool for Linux

1. **Clone the Visualization Tool Repository**:
   ```bash
   git clone https://github.com/berickcook/MinecraftEye.git
   ```
   **(Alternatively, run `visual_setup.sh` in the AIRIS directory)**
2. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r MinecraftEye/requirements.txt
   ```
3. **Edit Paths in `scene.py`**: Adjust lines 63-65 in `scene.py` to use the **full paths** for your setup. Also, confirm the client script points to the visual tool script correctly.
4. **Run Visualization Tool**:
   ```bash
   python MinecraftEye/main.py
   ```
5. **Navigate**: Use your mouse and keyboard to adjust the view if the AIRIS agent isn’t immediately visible.
---

## Important Notes

- **Exiting**: Use `Ctrl+C` in your shell to safely stop the AIRIS client.
- **Reconnect Option**: Use the `--restore` key to restore previous session of AIRIS 

---
