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
from enum import Enum, auto

from agent_idea import Coord,Grid,Player,State,Direction

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
            if (v != item):
                continue

            path_list = path_find((x,y))
            if (path_list is not None):
                return (x,y)
    return None

#Use BFS to find the shortest path
def path_find_full(target,accepted,debug=False):
    visited = set()
    visited_stones = set()

    start = ((player.x, player.y),' ',player.stones)
    first_element = ([start],0) 
    queue = [first_element]

    new_grid = Grid([['x']])
    new_grid.grid = copy.deepcopy(grid.grid)

    while queue:
        path = queue.pop(0)
        curr_pos = path[0][-1][0]

        for direction in [(0,1),(0,-1),(-1,0),(1,0)]:
            stones = path[0][-1][2]
            new_pos = (curr_pos[0]+direction[0],curr_pos[1]+direction[1])
            cell = grid[new_pos[1]][new_pos[0]]

            new_state = (new_pos[0],new_pos[1],stones)
            if (new_state in visited):
                continue
            visited.add(new_state)

            if (new_pos == target):
                return path[0]

            if (cell in accepted):
                if (cell == '~'):
                    stones -= 1
                    if (stones < 0 and not player.has_raft):
                        continue
                elif (cell == 'o'):
                    if (new_pos not in visited_stones):
                        visited_stones.add(new_pos)
                        stones += 1

                if (debug):
                    new_grid.set((new_pos[1],new_pos[0]),str(stones))
                    new_grid.print()

                #Increase the cost if not an empty spot
                #Encourage the player to take the easiest route
                cost = path[1]+1 if cell != ' ' and cell != 'O' else path[1]

                #If the player has a raft, try not to go back on land
                cost += 100 if cell == ' ' and player.on_raft else 0

                new_path = (path[0][:]+[(new_pos,cell,stones)],cost)
                queue.append(new_path)

        queue = sorted(queue, key=lambda x: x[1])
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

    raw_direction = (target[0]-player.x, target[1]-player.y)
    if (raw_direction in translation):
        direction = translation[raw_direction]
        commands += Direction.difference(current_direction, direction)

    for i,pos in enumerate(path[:-1],1):
        raw_direction = (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        direction = translation[raw_direction]

        commands += Direction.difference(current_direction, direction)
        commands += 'F'
        current_direction = direction

    return commands

def explore():
    print("Exploring")

    #Find every single unknown cell
    for y,line in enumerate(grid):
        for x,v in enumerate(line):
            if (v != 'X'):
                continue
            unknowns.append((x,y))
    if (player.target is not None):
        unknowns.insert(0,player.target)

    #Check if we can reach one of the unknowns
    for coord in unknowns:
        accepted = [' ','a','k','o','O','X']
        path_list = path_find_full(coord,accepted)

        if (path_list is None):
            continue
        player.target = coord;
        return path_to_commands(path_list,player,coord)+'F',state

    #If we can't reach any of the unknowns without crossing water, then we need a axe and a raft
    if (not player.has_axe):
        commands,state = axe();
    elif (not player.has_raft):
        commands,state = raft();
    return commands,state


def goal():
    print("Goaling")
    return None,None

#Function to take get action from AI or user
def get_actions(view):
    global grid
    global player
    global state

    if (grid is None):
        grid = Grid(view)
    else:
        #Check if the grid needs to be expanded
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
                if (grid[player.y+i][player.x+ii] != '+'):
                    grid.set((player.y+i,player.x+ii),view[i+2][ii+2])

    #print(len(grid[0]), len(grid))
    print("GRID")
    print(player.x, player.y, player.direction.name)
    #print_map(grid)
    grid.print()

    if (state == State.INITIAL):
        state = State.EXPLORE
    elif (state == State.EXPLORE):
        commands,state = explore()
        commands = commands[0:1]
    elif (state == State.EXPLORE):
        pass

    return commands

#Helper function to print the grid
def print_map(map):
    print('+'+'-'*len(map[0])+'+')
    for line in map:
        print('|'+''.join(line)+'|')
    print('+'+'-'*len(map[0])+'+')

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

    # navigates through grid with input stream of data
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
            actions = get_actions(view)
            actions_encoded = ''.join(actions).encode('utf-8')

            sock.send(actions_encoded)
            #time.sleep(0.1)

