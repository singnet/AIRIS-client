
# AIRIS Client - User Guide

## How to Run the AIRIS Client

### For Minecraft Setup

1. Install [CurseForge](https://www.curseforge.com/).
2. Install Minecraft (Fabric 1.20.1).
3. In CurseForge, search for and install the **Vereya Mod** and Fabric API.

### For AIRIS Client Setup

1. Install Python 3.10 from [Python Downloads](https://www.python.org/downloads/release/python-31011/). (Be sure to check the "Add Python to PATH" option during installation.)
2. Download the repository from [AIRIS Client GitHub](https://github.com/singnet/AIRIS-client).

#### Terminal Setup

1. Open a terminal in the downloaded repository folder.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
4. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Launch Minecraft and create a single-player game, enabling cheats in the world settings.

6. Run the AIRIS client:
   ```bash
   python minecraft_client.py --agent agent1qt05zd2vflz4vrytdyr2agz2775gv9e5hz99h06tq4uz6lv8fzq3k2dumzs
   ```

### For Visualization Tool

1. Download the visualization tool archive from [AIRIS Visual Tool](https://drive.google.com/file/d/1Th4T-ZFph-bJYlxVe1ZQA8MTl9X9YAmf/view?usp=sharing).
2. Extract all files into the AIRIS client directory.
3. After starting the AIRIS client script, launch `main.exe` in the client folder.
4. You may need to navigate to the correct location in the visualization window using your mouse and keyboard if the AIRIS agent doesn't immediately appear.
