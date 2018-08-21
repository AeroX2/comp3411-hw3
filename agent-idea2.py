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

direction_translation = {
    (0,-1): Direction.NORTH,
    (0,1): Direction.SOUTH,
    (-1,0): Direction.WEST,
    (1,0): Direction.EAST
}

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
        curr_pos_x,curr_pos_y,cost = path[-1]

        for direction in [(0,1),(0,-1),(-1,0),(1,0)]:
            new_pos = (curr_pos_x+direction[0],curr_pos_y+direction[1])

            #Check if we can move in this direction
            cell = grid.safe_get(new_pos)
            if (cell is None):
                continue

            new_state = (new_pos[0],new_pos[1])
            if (new_state in visited):
                continue
            visited.add(new_state)

            new_cost = cost
            if (cell not in ['X','o','-','k','a']):
                new_cost += 1
            new_state = (new_pos[0],new_pos[1],new_cost)

            new_path = path[:]+[new_state]
            if (cell in accepted):
                queue.append(new_path)

            #Check if we have reached the target
            if (new_pos == target):
                return new_path

        queue = sorted(queue, key=lambda x: x[-1][-1])
    return None

from collections import namedtuple 
PlayerState = namedtuple('PlayerState', ('x','y','stones','stones_hash','has_key','has_raft'))
GridState = namedtuple('GridState', ('picked_stones', 'placed_stones'))

#Use BFS to brute force a solution
def path_find_solve(target, last_player_state=None, last_grid_state=None):
    visited = set()

    start = PlayerState(player.x, player.y,
                        player.stones,
                        0,
                        player.has_key,
                        player.has_raft) if (last_player_state is None) else last_player_state
    grid_start = GridState(frozenset(),frozenset()) if (last_grid_state is None) else last_grid_state
    queue = [([start],grid_start)]

    hashc = lambda previous_hash, new_pos: hash((previous_hash, hash(new_pos)))

    while queue:
        state = queue.pop(0)
        path = state[0]
        player_state = path[-1]
        grid_state = state[1]

        for direction in [(0,1),(0,-1),(-1,0),(1,0)]:
            new_pos = (player_state.x+direction[0],player_state.y+direction[1])

            #Check if we can move in this direction
            cell = grid.safe_get(new_pos)
            if (cell is None):
                continue

            new_player_state = player_state._replace(x=new_pos[0],y=new_pos[1])
            new_picked_stones = set(grid_state.picked_stones)
            new_placed_stones = set(grid_state.placed_stones)

            if (cell == 'o'):
                if (not new_pos in new_picked_stones):
                    new_player_state = new_player_state._replace(stones=player_state.stones+1)
                    new_picked_stones.add(new_pos)
            elif (cell == '~'): 
                if (not new_pos in new_placed_stones):
                    new_player_state = new_player_state._replace(stones=player_state.stones-1,
                                                                 stones_hash=hashc(player_state.stones_hash, new_pos))
                    if (new_player_state.stones < 0):
                        continue
                    new_placed_stones.add(new_pos)
            elif (cell == '.' or 
                  cell == 'X' or
                  cell == '*'):
                continue

            if (new_player_state in visited):
                continue
            visited.add(new_player_state)

            new_grid_state = GridState(picked_stones=frozenset(new_picked_stones),
                                       placed_stones=frozenset(new_placed_stones))

            new_path = path[:]+[new_player_state]
            queue.append((new_path,new_grid_state))

            #Check if we have reached the target
            if (new_pos == target):
                return list(map(lambda p: (p.x, p.y), new_path)),new_path[-1],new_grid_state

        #queue = sorted(queue, key=lambda x: x[-1][-1])
    return None,None,None

#Convert a path to a command list
def path_to_commands(path, direction):

    commands = ''
    current_direction = direction

    for i,pos in enumerate(path[:-1],1):
        raw_direction = (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        direction = direction_translation[raw_direction]

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
    for (ux,uy) in unknowns:
        for coord in [(ux+x,uy+y) for x in range(-2,3) for y in range(-2,3)]:
            if (grid.safe_get(coord) != ' '):
                continue

            path_list = path_find_full(coord,accepted)

            #Path doesn't exist
            if (path_list is None):
                continue

            print("Going towards",coord)
            player.target = coord;
            return path_to_commands(path_list,player.direction),State.EXPLORE

    return [1,2,3],State.GOTO_TREASURE

def can_win():
    global player
    print("Checking if we can win")

    treasure = find_item(grid,'$')
    if (treasure is None and not player.has_treasure):
        return None,None

    print("Found treasure")
    key_path,last_player_state,last_grid_state = path_find_solve(treasure)
    if (key_path is None):
        print("Couldn't reach treasure")
        return None,None
    print("Can get treasure")

    home = (player.ix, player.iy)
    home_path,_,_ = path_find_solve(home, last_player_state, last_grid_state)
    if (home_path is None):
        print("Couldn't get back home")
        return None,None
    print("Can get back home")

    new_direction = direction_translation[(key_path[-1][0]-key_path[-2][0],key_path[-1][1]-key_path[-2][1])]
    key_commands = path_to_commands(key_path,player.direction)
    home_commands = path_to_commands(home_path,new_direction)
    
    return key_commands+home_commands,None

#Function to take get action from AI or user
def get_actions():
    #commands,state = can_win()
    #if (commands is None):
    #    commands,state = explore()
    #    commands = commands[0:1]

    commands,state = explore()
    commands = commands[0:1]
    if (state == State.GOTO_TREASURE):
        commands,state = can_win()

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

