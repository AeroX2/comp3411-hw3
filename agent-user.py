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

class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class State(Enum):
    INITIAL = auto()
    EXPLORE = auto()

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    #TODO CLEAN UP THESE DUMB FUNCTIONS
    @staticmethod
    def right(d):
        if (d == Direction.NORTH):
            return Direction.EAST
        elif (d == Direction.EAST):
            return Direction.SOUTH
        elif (d == Direction.SOUTH):
            return Direction.WEST
        elif (d == Direction.WEST):
            return Direction.NORTH

    @staticmethod
    def left(d):
        if (d == Direction.NORTH):
            return Direction.WEST
        elif (d == Direction.EAST):
            return Direction.NORTH
        elif (d == Direction.SOUTH):
            return Direction.EAST
        elif (d == Direction.WEST):
            return Direction.SOUTH

    @staticmethod
    def difference(d1,d2):
        diff = (d1.value - d2.value)
        if (diff == 1):
            return 'L'
        if (diff == -1):
            return 'R'
        if (diff == 3):
            return 'R'
        if (diff == -3):
            return 'L'
        if (diff == 2 or diff == -2):
            return 'RR'

class Player:
    #Player should always start in the 
    #middle of the 5 by 5 grid
    ix = 3
    x = 3
    iy = 3
    y = 3
    direction = Direction.NORTH

    def left(self):
        self.direction = Direction.left(self.direction)

    def right(self):
        self.direction = Direction.right(self.direction)

    def forward(self):
        if (self.direction == Direction.NORTH):
            self.y -= 1
        elif (self.direction == Direction.EAST):
            self.x += 1
        elif (self.direction == Direction.SOUTH):
            self.y += 1
        elif (self.direction == Direction.WEST):
            self.x -= 1

# Declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

map = None
state = State.INITIAL
player = Player()

def find_item(map, item):
    for line in map:
        try:
            line.index(item)
            return True
        except ValueError:
            pass
    return False

def expand_map(map, player):
    if (player.x-3 < 0):
        player.x += 1
        player.ix += 1
        for line in map:
            line.insert(0,'X')
    elif (player.x+3 > len(map[0])-1):
        for line in map:
            line.append('X')
    elif (player.y-3 < 0):
        player.y += 1
        player.iy += 1
        map.insert(0,['X' for _ in range(len(map[0]))])
    elif (player.y+3 > len(map)-1):
        map.append(['X' for _ in range(len(map[0]))])

def rotate_right(map):
    return [list(reversed(x)) for x in zip(*map)]

def rotate_left(map):
    #Lazy
    map = [list(reversed(x)) for x in zip(*map)]
    map = [list(reversed(x)) for x in zip(*map)]
    map = [list(reversed(x)) for x in zip(*map)]
    return map

def path_find(target,player,map):
    visited = set()
    queue = [[(player.x, player.y)]]

    while queue:
        path = queue.pop()
        curr_pos = path[-1]

        for direction in [(0,1),(0,-1),(-1,0),(1,0)]:
            new_pos = (curr_pos[0]+direction[0],curr_pos[1]+direction[1])
            if (new_pos in visited):
                continue
            visited.add(new_pos)

            if (new_pos == target):
                return path
            if (map[new_pos[1]][new_pos[0]] == ' '):
                new_path = list(path)
                new_path.append(new_pos)
                queue.append(new_path)
    return None

def path_to_commands(path, player):
    translation = {
        (0,-1): Direction.NORTH,
        (0,1): Direction.SOUTH,
        (-1,0): Direction.WEST,
        (1,0): Direction.EAST
    }

    current_direction = player.direction

    commands = ''
    for i,pos in enumerate(path[:-1],1):
        print(path[i], path[i-1])

        raw_direction = (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        direction = translation[raw_direction]
        print(direction)

        commands += Direction.difference(current_direction, direction)
        commands += 'F'
        current_direction = direction

    print(commands)
    import sys
    sys.exit()

    return list(commands)

def explore(map):
    while True:
        print('BLUB')
        print_grid(map)

        x = -1
        y = -1
        for y,v in enumerate(map):
            try:
                x = v.index('X')
                break
            except ValueError:
                pass

        if (x != -1 and y != -1):
            path_list = path_find((x,y),player,map)
            print("YEEE",path_list)
            if (path_list is not None):
                return path_to_commands(path_list,player)
            else:
                map[y][x] = 'C'
        else:
            print("Nowhere left to explore, PANIC!!!")
            return None

    return commands

# function to take get action from AI or user
def get_actions(view):
    global map
    global player
    global state

    if (map is None):
        map = copy.deepcopy(view)
        map.insert(0,['X' for _ in range(len(map[0]))])
        map.append(['X' for _ in range(len(map[0]))])
        for line in map:
            line.insert(0,'X')
            line.append('X')
    else:
        #Check if the map needs to be expanded
        expand_map(map, player)

        #Rotate the view map
        if (player.direction == Direction.EAST): 
            view = rotate_right(view)
        elif (player.direction == Direction.WEST): 
            view = rotate_left(view)
        elif (player.direction == Direction.SOUTH): 
            view = rotate_right(view)
            view = rotate_right(view)

        #Update the map
        for i in range(-2, 3):
            for ii in range(-2, 3):
                map[player.y+i][player.x+ii] = view[i+2][ii+2]

    #print(len(map[0]), len(map))
    print(player.x, player.y, player.direction.name)
    print("MAP")
    print_grid(map)

    #commands = explore(map)

    #commands = []
    #while True:
    #    if (state == State.INITIAL):
    #        pass
    #    elif (state == State.EXPLORE):
    #        if (find_item(map, '$')):
    #            state = State.GOTO_TREASURE
    #            break
    #        commands = explore()
    #        break
    #    elif (state == State.GOTO_TREASURE):
    #        commands = treasure()
    #        break

        #commands = explore()

    command = input()
    if (command == 'F'):
        player.forward()
    if (command == 'L'):
        player.left()
    if (command == 'R'):
        player.right()
    commands = [command]

    return commands

# helper function to print the grid
def print_grid(view):
    print('+'+'-'*len(map[0])+'+')
    for line in view:
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
            #print_grid(view) # COMMENT THIS OUT ON SUBMISSION
            actions = get_actions(view)
            action = actions[0]
            sock.send(action.encode('utf-8'))

    sock.close()
