import os
import json
import math
import pickle
import signal
import shutil
import base64
import argparse
from time import sleep, time

from tagilmo.utils.vereya_wrapper import MCConnector, RobustObserver
import tagilmo.utils.mission_builder as mb
from tagilmo.utils.mathutils import normAngle, degree2rad

import numpy as np

from airis_session import AirisSession, AgentAirisSession

API_URL = "http://127.0.0.1:8000/api"
session_running = True

def signal_handler(sig, frame):
    global session_running
    global mc
    session_running = False
    if 'mc' in globals():
        del mc

def signal_handler_dummy(sig, frame):
    pass

def get_cli_args():
    parser = argparse.ArgumentParser(description='Python client for executing AIRIS')
    parser.add_argument('--restore', action='store_true', help='Restore client session')
    parser.add_argument('--agent', type=str, help='The agent address to connect to')
    return parser.parse_args()

def read_session_id():
    file_path = 'session_id.json'
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} does not contain valid JSON.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    else:
        return data['session_id']

def save_session_id(session_id):
    file_path = 'session_id.json'
    try:
        with open(file_path, 'w') as file:
            json.dump({"session_id": session_id}, file)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def lookDir(rob, pitch, yaw):
    for t in range(3000):
        sleep(0.02)  # wait for action
        aPos = rob.waitNotNoneObserve('getAgentPos')
        dPitch = normAngle(degree2rad(pitch) - degree2rad(aPos[3]))
        dYaw = normAngle(degree2rad(yaw) - degree2rad(aPos[4]))
        if abs(dPitch) < 0.006 and abs(dYaw) < 0.006:
            sleep(0.02) # sleep
            break
        rob.sendCommand("turn " + str(dYaw * 0.4))
        rob.sendCommand("pitch " + str(dPitch * 0.4))
        sleep(0.02)
    rob.sendCommand("turn 0")
    rob.sendCommand("pitch 0")
    sleep(0.02)

def center(rob, pos, o_pitch, o_yaw):
    dist = lookAt(rob, pos)
    timeout = time()
    if dist > 0.2:
        rob.sendCommand('move .2')
    while dist > 0.2:
        if time() > timeout + 1:
            break
        dist = lookAt(rob, pos)
    rob.sendCommand('move 0')
    lookDir(rob, o_pitch, o_yaw)

def lookAt(rob, pos):
    pos = [pos[0] + .5, pos[1], pos[2] + .5]
    dist = 0
    timeout = time()
    for t in range(3000):
        sleep(0.02)
        aPos = rob.waitNotNoneObserve('getAgentPos')
        dist = math.sqrt((aPos[0] - pos[0]) * (aPos[0] - pos[0]) + (aPos[2] - pos[2]) * (aPos[2] - pos[2]))
        if dist < 0.5:
            break
        [pitch, yaw] = mc.dirToPos(aPos, pos)
        pitch = normAngle(pitch - degree2rad(aPos[3]))
        yaw = normAngle(yaw - degree2rad(aPos[4]))
        if abs(pitch) < 0.02 and abs(yaw) < 0.02: break
        rob.sendCommand("turn " + str(yaw * 0.4))
        rob.sendCommand("pitch " + str(pitch * 0.4))
        sleep(0.02)
        if time() > timeout + 1:
            break
    rob.sendCommand("turn 0")
    rob.sendCommand("pitch 0")
    sleep(0.02)
    return dist

def jump_forward(rob, stats):
    a_stats = [mc.getFullStat(key) for key in fullStatKeys]
    o_pitch = round(a_stats[3])
    o_yaw = round(a_stats[4]) % 360
    s_pos = [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2])]
    e_pos = s_pos
    match o_yaw:
        case 0:
            e_pos = [s_pos[0], s_pos[1], s_pos[2] + 1]
        case 45:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2] + 1]
        case 90:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2]]
        case 135:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2] - 1]
        case 180:
            e_pos = [s_pos[0], s_pos[1], s_pos[2] - 1]
        case 225:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2] - 1]
        case 270:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2]]
        case 315:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2] + 1]
    lookAt(rob, e_pos)
    rob.sendCommand('move 1')
    rob.sendCommand('jump 1')
    timeout = time()
    timedout = False
    while [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2])] != [e_pos[0], math.floor(stats[1]), e_pos[2]]:
        lookAt(rob, e_pos)
        if time() > timeout + 1:
            timedout = True
            break
        stats = [mc.getFullStat(key) for key in fullStatKeys]
    rob.sendCommand('move 0')
    rob.sendCommand('jump 0')
    sleep(.02)
    lookDir(rob, o_pitch, o_yaw)
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    old_stats = [mc.getFullStat(key) for key in fullStatKeys]
    sleep(.5)
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    while old_stats[1] != stats[1]:
        old_stats = [mc.getFullStat(key) for key in fullStatKeys]
        sleep(.05)
        stats = [mc.getFullStat(key) for key in fullStatKeys]
        if old_stats[1] == stats[1]:
            old_stats = [mc.getFullStat(key) for key in fullStatKeys]
            sleep(.05)
            stats = [mc.getFullStat(key) for key in fullStatKeys]

def move_forward(rob, stats):
    a_stats = [mc.getFullStat(key) for key in fullStatKeys]
    o_pitch = round(a_stats[3])
    o_yaw = round(a_stats[4]) % 360
    s_pos = [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2])]
    e_pos = s_pos
    match o_yaw:
        case 0:
            e_pos = [s_pos[0], s_pos[1], s_pos[2] + 1]
        case 45:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2] + 1]
        case 90:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2]]
        case 135:
            e_pos = [s_pos[0] - 1, s_pos[1], s_pos[2] - 1]
        case 180:
            e_pos = [s_pos[0], s_pos[1], s_pos[2] - 1]
        case 225:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2] - 1]
        case 270:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2]]
        case 315:
            e_pos = [s_pos[0] + 1, s_pos[1], s_pos[2] + 1]
    lookAt(rob, e_pos)
    rob.sendCommand('move 1')
    timeout = time()
    timedout = False
    while [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2])] != e_pos:
        lookAt(rob, e_pos)
        if time() > timeout + 1:
            timedout = True
            break
        stats = [mc.getFullStat(key) for key in fullStatKeys]
        if math.floor(stats[1]) != math.floor(e_pos[1]):
            break
    rob.sendCommand('move 0')
    sleep(.05)
    lookDir(rob, o_pitch, o_yaw)
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    old_stats = [mc.getFullStat(key) for key in fullStatKeys]
    sleep(.5)
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    while old_stats[1] != stats[1]:
        old_stats = [mc.getFullStat(key) for key in fullStatKeys]
        sleep(.05)
        stats = [mc.getFullStat(key) for key in fullStatKeys]
        if old_stats[1] == stats[1]:
            old_stats = [mc.getFullStat(key) for key in fullStatKeys]
            sleep(.05)
            stats = [mc.getFullStat(key) for key in fullStatKeys]

def main_loop(mc, rob, airis_session):
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    stats = [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2]), round(stats[3]), round(stats[4]) % 360]  # round(stats[4]) % 360]
    grid = mc.getNearGrid()
    environment_state = {
            'position':stats,
            'nearby_grid':grid
        }

    action, state_output, edges_output = airis_session.pre_action(environment_state)
    grid = np.array(grid)
    grid_3d = grid.reshape((5, 5, 5))
    grid_output = dict()

    for yi, y in enumerate(grid_3d):
        for zi, z in enumerate(grid_3d[yi]):
            for xi, x in enumerate(grid_3d[yi][zi]):
                if x != 'air':
                    grid_output[(stats[1] + yi - grid_origin_y, stats[2] + zi - grid_origin_z, stats[0] + xi - grid_origin_x)] = (stats[0] + xi - grid_origin_x, stats[1] + yi - grid_origin_y, stats[2] + zi - grid_origin_z, x)

    state_output, edges_output = base64.b64decode(state_output), base64.b64decode(edges_output)
    state_output, edges_output = pickle.loads(state_output), pickle.loads(edges_output)

    np.save('output/state_output_temp.npy', state_output)
    try:
        os.replace('output/state_output_temp.npy', 'output/state_output.npy')
    except PermissionError:
        pass

    np.save('output/edge_output_temp.npy', edges_output)
    try:
        os.replace('output/edge_output_temp.npy', 'output/edge_output.npy')
    except PermissionError:
        pass

    np.save('output/grid_output_temp.npy', np.array(grid_output))
    try:
        os.replace('output/grid_output_temp.npy', 'output/grid_output.npy')
    except PermissionError:
        pass

    match action:
        case 'move 0':
            lookDir(rob, 0, 0)
            move_forward(rob, stats)

        case 'move 45':
            lookDir(rob, 0, 45)
            move_forward(rob, stats)

        case 'move 90':
            lookDir(rob, 0, 90)
            move_forward(rob, stats)

        case 'move 135':
            lookDir(rob, 0, 135)
            move_forward(rob, stats)

        case 'move 180':
            lookDir(rob, 0, 180)
            move_forward(rob, stats)

        case 'move 225':
            lookDir(rob, 0, 225)
            move_forward(rob, stats)

        case 'move 270':
            lookDir(rob, 0, 270)
            move_forward(rob, stats)

        case 'move 315':
            lookDir(rob, 0, 315)
            move_forward(rob, stats)

        case 'jump 0':
            lookDir(rob, 0, 0)
            jump_forward(rob, stats)

        case 'jump 45':
            lookDir(rob, 0, 45)
            jump_forward(rob, stats)

        case 'jump 90':
            lookDir(rob, 0, 90)
            jump_forward(rob, stats)

        case 'jump 135':
            lookDir(rob, 0, 135)
            jump_forward(rob, stats)

        case 'jump 180':
            lookDir(rob, 0, 180)
            jump_forward(rob, stats)

        case 'jump 225':
            lookDir(rob, 0, 225)
            jump_forward(rob, stats)

        case 'jump 270':
            lookDir(rob, 0, 270)
            jump_forward(rob, stats)

        case 'jump 315':
            lookDir(rob, 0, 315)
            jump_forward(rob, stats)
    sleep(1)
    stats = [mc.getFullStat(key) for key in fullStatKeys]
    stats = [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2]), round(stats[3]), round(stats[4]) % 360]  # round(stats[4]) % 360]
    grid = mc.getNearGrid()
    environment_state = {
        'position':stats,
        'nearby_grid':grid
    }
    # Post-Action API call goes here
    try:
        airis_session.post_action(environment_state,)
    except:
        pass


if __name__ == '__main__':

    args = get_cli_args()
    if args.restore:
        session_id = read_session_id()
    signal.signal(signal.SIGINT, signal_handler_dummy)

    args = get_cli_args()
    if args.restore:
        session_id = read_session_id()
    signal.signal(signal.SIGINT, signal_handler_dummy)

    if not os.path.exists('output'):
        # If it doesn't exist, create it
        os.makedirs('output')
    else:
        # If it exists, empty its contents
        for filename in os.listdir('output'):
            file_path = os.path.join('output', filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    miss = mb.MissionXML()

    world = mb.defaultworld(
        seed='5',
        forceReset="false",
        forceReuse="true")
    miss.setWorld(world)

    mc = MCConnector(miss)
    mc.safeStart()

    rob = RobustObserver(mc)

    fullStatKeys = ['XPos', 'YPos', 'ZPos', 'Pitch', 'Yaw']

    rob.sendCommand('chat /gamemode creative')
    rob.sendCommand('chat /effect give @s minecraft:night_vision infinite 0 true')
    sleep(5)
    rob.sendCommand('chat /difficulty peaceful')
    sleep(5)
    rob.sendCommand('Starting!')

    grid_origin_x = 2
    grid_origin_y = 2
    grid_origin_z = 2

    stats = [mc.getFullStat(key) for key in fullStatKeys]
    stats = [math.floor(stats[0]), math.floor(stats[1]), math.floor(stats[2]), round(stats[3]), 0]  # round(stats[4]) % 360]
    grid = mc.getNearGrid()

    # Initialization API call goes here
    goal = {'type': 'explore'}
    actions = ['move 0', 'move 45', 'move 90', 'move 135', 'move 180', 'move 225', 'move 270', 'move 315', 'jump 0', 'jump 45', 'jump 90', 'jump 135', 'jump 180', 'jump 225', 'jump 270', 'jump 315']

    if args.agent:
        airis_session = AgentAirisSession(args.agent)
    else:
        airis_session = AirisSession(api_url=API_URL)

    airis_session.initialize_session(goal, actions)

    signal.signal(signal.SIGINT, signal_handler)

    while session_running:
        try:
            main_loop(mc, rob, airis_session)
        except NameError:
            pass

    session_id = airis_session.end_session()
    if session_id:
        save_session_id(session_id)
