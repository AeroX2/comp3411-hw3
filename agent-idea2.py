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

def find_all_closest_item(item):
    coords = [(x,y) for y,line in enumerate(grid) for x,v in enumerate(line) if v == item]
    coords = sorted(coords, key=lambda x: abs(x[0]-player.x)+abs(x[1]-player.y))
    return coords

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
            #if (player.on_raft and cell != '~'):
            #    new_cost += 100

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
PlayerState = namedtuple('PlayerState', ('x','y',
                                         'stones',
                                         'stones_hash',
                                         'has_key',
                                         'has_axe',
                                         'has_raft',
                                         'on_water',
                                         'destinations_reached'))
GridState = namedtuple('GridState', ('picked_stones',
                                     'placed_stones',
                                     'unlocked_doors',
                                     'cut_trees'))

#Use BFS to brute force a solution
def path_find_solve(destinations, last_player_state=None, last_grid_state=None):
    visited = set()

    start = PlayerState(player.x, player.y,
                        player.stones,
                        0,
                        player.has_key,
                        player.has_axe,
                        player.has_raft,
                        player.on_water,
                        0) if (last_player_state is None) else last_player_state
    grid_start = GridState(frozenset(),
                           frozenset(),
                           frozenset(),
                           frozenset()) if (last_grid_state is None) else last_grid_state
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
            new_unlocked_doors = set(grid_state.unlocked_doors)
            new_cut_trees = set(grid_state.cut_trees)


            if (cell != '~' and player_state.on_water):
                new_player_state = new_player_state._replace(on_water=False,
                                                             has_raft=False)

            if (cell == 'o'):
                if (not new_pos in new_picked_stones):
                    new_player_state = new_player_state._replace(stones=player_state.stones+1)
                    new_picked_stones.add(new_pos)
            elif (cell == '~'): 
                if (player_state.stones > 0):
                    #print("Placing stone")
                    if (not new_pos in new_placed_stones):
                        new_player_state = new_player_state._replace(stones=player_state.stones-1,
                                                                     stones_hash=hashc(player_state.stones_hash, new_pos))
                        new_placed_stones.add(new_pos)
                        #print(new_placed_stones)

                    if (new_player_state.stones < 0):
                        continue
                elif (player_state.has_raft):
                    #print("Using raft at",new_pos)
                    new_player_state = new_player_state._replace(on_water=True)
                else:
                    continue
            elif (cell == 'k'):
                #print("Found key")
                new_player_state = new_player_state._replace(has_key=True)
            elif (cell == '-'):
                if (not player_state.has_key and not new_pos in new_unlocked_doors):
                    continue
                #print("Unlocked door")
                new_player_state = new_player_state._replace(has_key=False)
                new_unlocked_doors.add(new_pos)
            elif (cell == 'a'):
                new_player_state = new_player_state._replace(has_axe=True)
            elif (cell == 'T'):
                #print("Tree")
                #print(player_state)
                #print(new_player_state)

                if (not player_state.has_axe):
                    continue
                if (new_player_state.on_water):
                    continue
                if (not new_pos in new_cut_trees):
                    new_player_state = new_player_state._replace(has_raft=True)
                    new_cut_trees.add(new_pos)
            elif (cell == '.' or 
                  cell == 'X' or
                  cell == '*'):
                continue

            if (new_pos == destinations[player_state.destinations_reached]):
                new_player_state = new_player_state._replace(destinations_reached=player_state.destinations_reached+1)
                #print("Destination reached!")
                #print(new_player_state)

            if (new_player_state in visited):
                continue
            visited.add(new_player_state)

            new_grid_state = GridState(picked_stones=frozenset(new_picked_stones),
                                       placed_stones=frozenset(new_placed_stones),
                                       unlocked_doors=frozenset(new_unlocked_doors),
                                       cut_trees=frozenset(new_cut_trees))

            new_path = path[:]+[new_player_state]
            queue.append((new_path,new_grid_state))

            #Check if we have reached the target
            if (new_player_state.destinations_reached >= len(destinations)):
                return list(map(lambda p: (p.x, p.y), new_path)),new_player_state,new_grid_state

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

        cell = grid.safe_get(path[i])
        if (cell == 'T'):
            commands += 'C'
        if (cell == '-'):
            commands += 'U'

        commands += 'F'
        current_direction = direction

    return commands

def explore():
    print("Exploring")

    accepted = [' ','a','k','o','O','$']
    if (player.has_axe):
        accepted.append('T')
    if (player.has_key):
        accepted.append('-')
    if (player.has_raft and not player.on_water):
        accepted.append('~')
    if (player.on_raft):
        accepted = ['~']

    #Find all the unknowns and sort them by distance from the player
    unknowns = find_all_closest_item('X')
    if (player.target == (player.x,player.y) or 
        grid.safe_get(player.target) not in accepted):
        player.target = None
    if (player.target is not None):
        #print("Using previous")

        #unknowns.insert(0,player.target)
        path_list = path_find_full(player.target,accepted+['X'])
        if (path_list is not None):
            commands = path_to_commands(path_list,player.direction)
            return commands,State.EXPLORE

    #Check if we can reach one of the areas around the unknowns
    for (ux,uy) in unknowns:
        for coord in [(ux+x,uy+y) for x in range(-2,3) for y in range(-2,3)]:
            if (grid.safe_get(coord) not in accepted):
                continue

            path_list = path_find_full(coord,accepted+['X'])

            #Path doesn't exist
            if (path_list is None):
                continue

            #print(unknowns)
            print("Going towards:",coord)
            print("Because:",(ux,uy))
            #print("Path list:",path_list)

            player.target = coord
            commands = path_to_commands(path_list,player.direction)
            return commands,State.EXPLORE

    return None,State.GOTO_AXE

def axe():
    print("Axing")

    accepted = [' ','k','o','O','a']

    axes = find_all_closest_item('a')
    axe_path = None
    for axe in axes:
        axe_path = path_find_full(tree,accepted)
        if (axe_path is not None):
            break
    if (axe_path is None):
        return None,State.GOTO_TREE

    return path_to_commands(axe_path,player.direction),State.GOTO_TREE

def tree():
    print("Treeing")
    if (not player.has_axe):
        return None,State.GOTO_TREASURE

    accepted = [' ','k','o','O','T']
    trees = find_all_closest_item('T')
    tree_path = None

    for tree in trees:
        tree_path = path_find_full(tree,accepted)
        if (tree_path is not None):
            break
    if (tree_path is None):
        return None,State.GOTO_TREASURE

    return path_to_commands(tree_path,player.direction),State.EXPLORE

def stone():
    print("Stoning")

    accepted = [' ','k','o','O']
    stones = find_all_closest_item('o')
    stone_path = None

    for stone in stones:
        stone_path = path_find_full(stone,accepted)
        if (stone_path is not None):
            break
    if (stone_path is None):
        return None,State.GOTO_TREASURE
    return path_to_commands(stone_path,player.direction),State.EXPLORE

def can_win():
    global player
    print("Checking if we can win")

    treasure = find_item(grid,'$')
    if (treasure is None):
        return None,None
    print("Found treasure")

    home = (player.ix,player.iy)
    if (not player.has_treasure):
        full_path,_,_ = path_find_solve([treasure,home])
        if (full_path is None):
            print("Couldn't reach treasure or home")
            return None,None
        print("Can get treasure and back home")

        full_commands = path_to_commands(full_path,player.direction)
        return full_commands,None

    home_path,_,_ = path_find_solve([home])
    if (home_path is None):
        print("Couldn't get back home")
        return None,None
    print("Can get back home")

    home_commands = path_to_commands(home_path,new_direction)
    return home_commands,None

#Function to take get action from AI or user
def get_actions():
    #commands,state = can_win()
    #if (commands is None):
    #    commands,state = explore()
    #    commands = commands[0:1]

    global state

    #commands,state = axe()
    #if (commands is not None):
    #    return commands

    #commands,state = tree()
    #if (commands is not None):
    #    return commands

    commands,state = stone()
    if (commands is not None):
        return commands

    commands,state = explore()
    if (commands is not None):
        commands = commands[0:1]
        return commands

    commands,state = can_win()
    if (commands is not None):
        return commands

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

