#!/usr/bin/python3
# ^^ note the python directive on the first line
# COMP 9414 agent initiation file 
# requires the host is running before the agent
# designed for python 3.6
# typical initiation would be (file in working directory, port = 31415)
#        python3 agent.py -p 31415
# created by Leo Hoare
# with slight modifications by Alan Blair

import sys
import copy
import socket

from agent_idea import Coord,Grid,Player,State,Direction

#Helper function to print the grid
def print_map(map):
    print('+'+'-'*len(map[0])+'+')
    for line in map:
        print('|'+''.join(line)+'|')
    print('+'+'-'*len(map[0])+'+')

def rotate_right(view):
    return [list(reversed(x)) for x in zip(*view)]

def rotate_left(view):
    return list(zip(*[reversed(x) for x in view]))

# Declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

grid = None
state = State.EXPLORE
player = Player()

#Find an item in the grid
def find_item(grid, item):
    for y,line in enumerate(grid):
        for x,v in enumerate(line):
            if (v == item):
                return (x,y)
    return None

#Use BFS to find the shortest path
def path_find_full(target,accepted,player_p=None):
    visited = set()

    if (player_p is None):
        start = (player.x, player.y, 0)
    else:
        start = (player_p.x, player_p.y, 0)
    queue = [[start]]

    while queue:
        path = queue.pop(0)
        curr_pos_x,curr_pos_y,cost_past_obstacle = path[-1]

        for direction in [(0,1),(0,-1),(-1,0),(1,0)]:
            new_pos = (curr_pos_x+direction[0],curr_pos_y+direction[1])

            #Check if we can move in this direction
            cell = grid.safe_get(new_pos)
            if (cell is None):
                continue;

            new_state = (new_pos[0],new_pos[1],cost_past_obstacle) #(new_pos,player_state)
            if (cost_past_obstacle > 0):
                new_state = (new_pos[0],new_pos[1],cost_past_obstacle+1) #(new_pos,player_state)

            if (new_state in visited):
                continue
            visited.add(new_state)

            new_path = path[:]+[new_state]
            if (cell in accepted or cost_past_obstacle > 0):
                queue.append(new_path)
            else:
                new_state = (new_pos[0],new_pos[1],1) #(new_pos,player_state)
                new_path = path[:]+[new_state]
                queue.append(new_path)

            #Check if we have reached the target
            if (new_pos == target):
                return new_path
        queue = sorted(queue, key=lambda x: x[-1][-1])
    return None

#Convert a path to a command list
def path_to_commands(path, player, target):
    translation = {
        (0,-1): Direction.NORTH,
        (0,1): Direction.SOUTH,
        (-1,0): Direction.WEST,
        (1,0): Direction.EAST
    }

    current_direction = player.direction
    commands = ''

    #raw_direction = (target[0]-player.x, target[1]-player.y)
    #if (raw_direction in translation):
    #    direction = translation[raw_direction]
    #    #commands += Direction.difference(current_direction, direction)

    for i,pos in enumerate(path[:-1],1):
        raw_direction = (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        direction = translation[raw_direction]

        commands += Direction.difference(current_direction, direction)
        commands += 'F'
        current_direction = direction

    return commands

def explore():
    print("Exploring")

    #Find all the unknowns and sort them by distance from the player
    unknowns = [(x,y) for y,line in enumerate(grid) for x,v in enumerate(line) if v == 'X']
    unknowns = sorted(unknowns, key=lambda x: abs(x[0]-player.x)+abs(x[1]-player.y))
    if (player.target is not None and grid.safe_get(player.target) == 'X'):
        unknowns.insert(0,player.target)

    #Check if we can reach one of the unknowns
    accepted = [' ','a','k','o','O','X']
    for coord in unknowns:
        path_list = path_find_full(coord,accepted)

        #Path doesn't exist
        if (path_list is None):
            continue

        last = path_list[-1]

        #Too many obstacles, ie (cost too high)
        if (last[-1] > 3):
            pass
            #continue


        last = list(filter(lambda x: x[-1] <= 0, path_list))[-1]
        #Outside view range
        if (max(abs(last[0]-coord[0]),abs(last[1]-coord[1])) > 2):
            print(coord, path_list)
            continue

        print("Going towards",coord)
        player.target = coord;
        return path_to_commands(path_list,player,coord),State.EXPLORE

    #accepted = [' ','a','k','o','O','X','~']
    #for coord in unknowns:
    #    path_list = path_find_full(coord,accepted)
    #    if (path_list is None):
    #        continue

    #    player.target = coord;
    #    return path_to_commands(path_list,player,coord)+'F',State.EXPLORE

    #If we can't reach any of the unknowns without crossing water, then we need a axe and a raft
    if (not player.has_axe):
        commands,state = axe();
    elif (not player.has_raft):
        commands,state = raft();
    return commands,state

def can_win():
    global player
    print("Checking if we can win")

    treasure = find_item(grid,'$')
    if (treasure is None and not player.has_treasure):
        return None,None

    print("Found treasure")

    accepted = [' ','a','k','o','O']
    if (player.has_raft):
        accepted.append('~')
    if (player.has_key):
        accepted.append('-')

    key_path_list = path_find_full(treasure,accepted)
    if (key_path_list is None or key_path_list[-1][-1] > 0):
        return None,None
    print("Can get treasure")

    key_commands = path_to_commands(key_path_list,player,treasure)

    temp_player = copy.deepcopy(player)
    for c in key_commands:
        if c == 'F':
            temp_player.forward(grid)
        elif c == 'L':
            temp_player.left()
        elif c == 'R':
            temp_player.right()

    home = (player.ix, player.iy)
    home_path_list = path_find_full(home,accepted,temp_player)
    if (home_path_list is None or home_path_list[-1][-1] > 0):
        return None,None

    print("Can get back home")


    return key_commands+path_to_commands(home_path_list,temp_player,home),None

#Function to take get action from AI or user
def get_actions():
    commands,state = can_win()
    if (commands is None):
        commands,state = explore()
        commands = commands[0:1]
    return commands

def update(command, view):
    global grid
    global player
    global state

    if (command == 'F'):
        player.forward(grid)
    elif (command == 'L'):
        player.left()
    elif (command == 'R'):
        player.right()
    elif (command == 'C'):
        player.cut()

    #Check if the grid needs to be expanded
    if (grid is None):
        grid = Grid(view)
    grid.expand_map(player)

    #Rotate the view grid
    if (player.direction == Direction.EAST): 
        view = rotate_right(view)
    elif (player.direction == Direction.WEST): 
        view = rotate_left(view)
    elif (player.direction == Direction.SOUTH): 
        view = rotate_right(view)
        view = rotate_right(view)

    #Update the grid
    for i in range(-2, 3):
        for ii in range(-2, 3):
            grid.set((player.y+i,player.x+ii),view[i+2][ii+2])

    print("GRID")
    print(player.x, player.y, player.direction.name)
    grid.print()

if __name__ == "__main__":
    # checks for correct amount of arguments 
    if len(sys.argv) != 3:
        print("Usage Python3 "+sys.argv[0]+" -p port \n")
        sys.exit(1)

    port = int(sys.argv[2])

    # checking for valid port number
    if not 1025 <= port <= 65535:
        print('Incorrect port number')
        sys.exit()

    # creates TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
         # tries to connect to host
         # requires host is running before agent
         sock.connect(('localhost',port))
    except (ConnectionRefusedError):
         print('Connection refused, check host is running')
         sys.exit()

    import time
    previous_actions = ['']

    # Navigates through grid with input stream of data
    i=0
    j=0
    while True:
        data = sock.recv(100)
        if not data:
            sys.exit()

        for ch in data:
            if (i == 2 and j == 2):
                view[i][j] = '^'
                view[i][j+1] = chr(ch)
                j+=1 
            else:
                view[i][j] = chr(ch)
            j+=1
            if (j > 4):
                j=0
                i=(i+1)%5

        if (j == 0 and i == 0):
            update(previous_actions[0], view)
            previous_actions = previous_actions[1:]

            if (len(previous_actions) <= 0):
                previous_actions = get_actions()
                print(previous_actions)
            sock.send(previous_actions[0].encode('utf-8'))
            #time.sleep(0.1)

