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

class Grid:
    grid = []

    def __init__(self, view):
        self.grid = copy.deepcopy(view)
        self.grid.insert(0,['X' for _ in range(len(self.grid[0]))])
        self.grid.append(['X' for _ in range(len(self.grid[0]))])
        for line in self.grid:
            line.insert(0,'X')
            line.append('X')

    def __getitem__(self, index):
        if (isinstance(self.grid[0], list)):
            return self.grid[index]
        return self.grid[index]

    def safe_get(self, coord):
        try:
            return self.grid[coord[1]][coord[0]]
        except:
            return None

    def set(self,tup,value):
        self.grid[tup[0]][tup[1]] = value

    def expand_map(self, player):
        if (player.x-3 < 0):
            player.x += 1
            player.ix += 1
            for line in self.grid:
                line.insert(0,'X')
        elif (player.x+3 > len(self.grid[0])-1):
            for line in self.grid:
                line.append('X')
        elif (player.y-3 < 0):
            player.y += 1
            player.iy += 1
            self.grid.insert(0,['X' for _ in range(len(self.grid[0]))])
        elif (player.y+3 > len(self.grid)-1):
            self.grid.append(['X' for _ in range(len(self.grid[0]))])

    def print(self):
        print_map(self.grid)

class State(Enum):
    INITIAL = auto()
    EXPLORE = auto()
    GOAL = auto()
    NO_GOAL_FOUND = auto()
    GOTO_TREASURE = auto()
    GOTO_KEY = auto()
    GOTO_AXE = auto()
    GOTO_STONE = auto()
    GO_HOME = auto()
    PANIC = auto()

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
        if (diff == 0):
            return ''
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
    #middle of the 5 by 5 grid but unknown 'X's surround the grid
    x = 3
    y = 3
    ix = 3
    iy = 3

    px = 3
    py = 3

    target = None
    direction = Direction.NORTH
    stones = 0

    has_treasure = False
    has_raft = False
    has_key = False
    has_axe = False

    on_water = False
    on_raft = False

    def left(self):
        self.direction = Direction.left(self.direction)

    def right(self):
        self.direction = Direction.right(self.direction)

    def forward(self, grid):
        if (self.direction == Direction.NORTH):
            self.y -= 1
        elif (self.direction == Direction.EAST):
            self.x += 1
        elif (self.direction == Direction.SOUTH):
            self.y += 1
        elif (self.direction == Direction.WEST):
            self.x -= 1

        cell = grid[self.y][self.x]
        if (cell == 'a'):
            self.has_axe = True
        elif (cell == 'k'):
            self.has_key = True
        elif (cell == '$'):
            self.has_treasure = True
        elif (cell == 'o'):
            self.stones += 1
        elif (cell == '~'):
            self.on_water = True
            if (self.stones > 0):
                self.stones -= 1
            else:
                self.on_raft = True
        elif ((cell == ' ' or cell == 'O') and self.on_water):
            if (self.on_raft):
                self.on_raft = False
                self.has_raft = False
            self.on_water = False

    def cut(self):
        self.has_raft = True

def rotate_right(view):
    return [list(reversed(x)) for x in zip(*view)]

def rotate_left(view):
    return list(zip(*[reversed(x) for x in view]))

# Declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

grid = None
state = State.INITIAL
player = Player()

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
def path_find(target):
    accepted = [' ','+','a','k','o','O']
    if (player.has_raft or player.stones > 0):
        accepted.append('~')

    path = path_find_full(target,accepted)
    if (path is None):
        return None
    return list(map(lambda x: x[0], path))

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

    #goal_coord = find_item(grid,goals[-1])
    #if (goal_coord is not None):
    #    if (path_find_full(goal_coord,accepted=[' ','T','-','~','a','k','o']) is not None):
    #        return None,State.GOAL

    #Find every single unknown cell
    unknowns = []
    for y,line in enumerate(grid):
        for x,v in enumerate(line):
            if (v != ' '):
                continue

            do_it = False
            for x2 in range(-3,4):
                for y2 in range(-3,4):
                    new_pos = (x+x2,y+y2)
                    if (grid.safe_get(new_pos) == 'X'):
                        do_it = True
                        break
                if (do_it):
                    break

            if (do_it):
                unknowns.append((x,y))

            #elif (v == 't'):
            #    unknowns = [(x,y)]
            #    break

    #Sort by distance
    #Has a problem where it gets stuck between 2 points flickering between them
    #sample/s2.in
    #unknowns = sorted(unknowns, key=lambda x: abs(x[0]-player.x)+abs(x[1]-player.y))

    #Check if we can reach one of the unknowns
    for coord in unknowns:
        temp = player.stones
        player.stones = -10000
        path_list = path_find(coord)
        player.stones = temp

        if (path_list is None):
            continue
        return path_to_commands(path_list,player,coord)+'F',state

    #Haven't found our goal yet, try everything to explore more
    return None,State.NO_GOAL_FOUND

def goal():
    print("Goaling")

    #goal = goals[-1]

    ##Check if the goal
    #if (goal == '-'):
    #    commands,state = key()
    #    if (commands is not None):
    #        return commands,state
    #elif (goal == '$'):
    #    commands,state = treasure()
    #    if (commands is not None):
    #        return commands,state
    #elif (goal == 'h'):
    #    commands,state = home()
    #    if (commands is not None):
    #        return commands,state

    ##Check if we can reach the goal at all
    #goal_coord = find_item(grid,goal)
    #path = path_find_full(goal_coord,accepted=[' ','T','-','~','a','k','o'])

    #if (path is not None): #Check what we need to reach our goal
    #    obstacles = filter(lambda x: x != ' ', map(lambda x: x[1], path))
    #    obstacles = list(obstacles)
    #    print(obstacles)
    #    if (obstacles):
    #        import pdb
    #        pdb.set_trace()
    #        goals.append(obstacles[-1])
    #        return None,state

    #If we cant reach our goal at all we need to explore more
    #Lets check if we can cut down some trees
    commands,state = axe()
    if (commands is not None):
        return commands,state
    #Else just normally explore

    return None,State.EXPLORE

def no_goal_found():
    print("No goal found")

    commands,state = key()
    if (commands is not None):
        return commands,state

    commands,state = stone()
    if (commands is not None):
        return commands,state

    commands,state = axe()
    if (commands is not None):
        return commands,state

    commands,state = treasure()
    if (commands is not None):
        return commands,state

    if (player.has_treasure):
        commands,state = home()
        if (commands is not None):
            return commands,state

    commands,state = explore()
    if (commands is not None):
        return commands,State.EXPLORE

    #Nothing left to do
    #This is the end
    print("Tried everything, nothing left to do")
    import sys
    sys.exit()

def treasure():
    print("Treasuring")

    coord = find_item(grid,'$')
    if (coord is None):
        return None,State.GOAL

    path_list = path_find(coord)
    if (path_list is None):
        return None,State.GOAL

    return path_to_commands(path_list, player,coord)+'F',state

def key():
    print("Keying")

    coord = find_item(grid,'k')
    if (coord is None and not player.has_key):
        return None,State.GOAL

    path_list = path_find(coord)
    command_list = None
    if (path_list is not None):
        command_list = path_to_commands(path_list, player, coord)
    if (coord is not None and len(command_list) == 0):
        return 'F',state

    if (player.has_key):
        coord = find_item(grid,'-')
        path_list = path_find(coord)
        if (path_list is None):
            return None,State.GOAL
        return path_to_commands(path_list, player, coord)+'U',state

    return path_to_commands(path_list, player, coord),state


def axe():
    print("Axing")

    coord = find_item(grid,'a')
    if (coord is None and not player.has_axe):
        return None,State.GOAL

    path_list = path_find(coord)
    command_list = None
    if (path_list is not None):
        command_list = path_to_commands(path_list, player, coord)
    if (coord is not None and len(command_list) == 0):
        return 'F',state

    if (player.has_axe):
        coord = find_item(grid,'T')
        if (coord is None):
            return None,State.EXPLORE

        accepted = [' ','a','k','o','O']
        path_list = path_find_full(coord,accepted)
        if (path_list is None):
            return None,State.EXPLORE
        path_list = list(map(lambda x: x[0], path_list))

        return path_to_commands(path_list, player, coord)+'C',state

    return path_to_commands(path_list,player, coord),state

def stone():
    print("Stoning")

    #coord = find_item(grid,'o')
    #if (coord is None):
    #    return None,State.GOAL

    coord = None
    for y,line in enumerate(grid.grid):
        for x,v in enumerate(line):
            if (v == '$'):
                coord = (x,y)
                break
    
    accepted = [' ','+','a','k','o','O','~']
    path = path_find_full(coord,accepted,debug=True)
    #grid.print()
    print(path)

    #if (path is None):
    #    return None
    path_list = list(map(lambda x: x[0], path))


    #coord = find_item(grid,'o')
    #if (coord is None):
    #    return None,State.GOAL

    import time
    time.sleep(1)

    return path_to_commands(path_list, player,coord)+'F',state

def home():
    coord = (player.ix, player.iy)
    path_list = path_find(coord)
    if (path_list is None):
        return None,State.GOAL
    return path_to_commands(path_list, player, coord)+'F',state

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

    commands = None
    for iteration in range(11):
        if (state == State.INITIAL):
            state = State.EXPLORE
        elif (state == State.EXPLORE):
            commands,state = explore()
        elif (state == State.GOAL):
            commands,state = goal()
        elif (state == State.NO_GOAL_FOUND):
            commands,state = no_goal_found()
        elif (state == State.GOTO_TREASURE):
            commands,state = treasure()
        elif (state == State.GOTO_KEY):
            commands,state = key()
        elif (state == State.GOTO_AXE):
            commands,state = axe()
        elif (state == State.GOTO_STONE):
            commands,state = stone()
        elif (state == State.GO_HOME):
            commands,state = home()
        else:
            print("YOU DIDNT DEFINE A STATE")
            import sys
            sys.exit()

        if (commands is not None):
            break

    if (iteration >= 10):
        print("ERROR: TOO MANY ITERATIONS")
        import sys
        sys.exit()

    #commands = input()
    command = commands[0]
    if (command == 'F'):
        player.forward(grid)
    elif (command == 'L'):
        player.left()
    elif (command == 'R'):
        player.right()
    elif (command == 'C'):
        player.cut()

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
            #print_grid(view) # COMMENT THIS OUT ON SUBMISSION
            actions = get_actions(view)
            action = actions[0]
            print(action)

            sock.send(action.encode('utf-8'))
            #time.sleep(0.1)

    sock.close()
