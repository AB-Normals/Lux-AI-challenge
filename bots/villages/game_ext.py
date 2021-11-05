# GameExtended
# ---
# The Game class with steroids

import math
import weakref
from typing import Tuple, List, Dict

from lux.game import Game
from lux.game_map import Position, Cell
from lux.constants import Constants
from lux.game_objects import Unit

DIRECTIONS = Constants.DIRECTIONS
RESOURCE_TYPES = Constants.RESOURCE_TYPES

class Task:
    """
    Each task consist on a type of Job for a single unit.
    The Task has to be done on a specified position, so the task is always 
    movement and then the Job
    """
    SLEEP = "r"         # Sleep until daytime
    BUILD = "b"         # Build a citytile of city 'city_id' at 'pos' 
    HARVEST = "h"       # Get resouce at 'pos'
    ENERGIZE = "e"      # Feed a 'city_id' with resource ad return it at 'pos'
    EXPLORE = "x"       # Search for a place to build a new city

def TaskStr(task: str) -> str:
    _strings_ = {
        Task.SLEEP: "SLP",
        Task.BUILD: "BLD",
        Task.HARVEST: "HRV",
        Task.ENERGIZE: "NRG",
        Task.EXPLORE: "XPL"
    }

    return(_strings_[task])


class Job:
    def __init__(self, task: str, pos: Position):
        self.pos: Position = pos    # some task need a position reference
        self.task: str = task       # task type
        self.city_id: str = ""      # city_id parameter used by some tasks
        self.unit_id: str = ""      # unit_id that has this task as assignement
        self.subtask: int = 0       # subtask used by jobs with multistate tasks 

    def __str__(self):
        return f"{self.unit_id}: {TaskStr(self.task)} {self.pos} c:{self.city_id}"

class JobBoard:
    """
    This is a Bulletin Board with 3 different lists:
    - todo : list of jobs no-one has in charge
    - inprogress : jobs currently in progress (with unit who has the assignement)
    - done : completed jobs (only for debug pouposes) 
    """

    def __init__(self, parent):
        self.todo: List = []        # ToDo Jobs
        self.inprogress: Dict = {}  # InProgress Jobs
        self.done: List = []        # Done Jobs
        self.rip: List = []         # Dead Units
        self.parent = parent

    def _nextJob(self, pos: Position = None):
        # TODO: need a heuristics for job selection based on different parameters:
        #       as unit position, time of day, priority.
        #       Now no heurostics
        if self.todo:
            closest_dist = math.inf
            i = 0
            for n in range(len(self.todo)):
                dist = pos.distance_to(self.todo[n].pos)
                if dist < closest_dist:
                    i = n
                    dist = closest_dist            
            return self.todo.pop(i)
        else:
            # TODO: choose a default Job
            return None

    def _activeJobs(self):
        """ Return a list with all active Jobs (not DONE) """
        return self.todo + [n for n in self.inprogress.values()]

    def addJob(self, task: str, pos: Position, city_id: str = "") -> bool:
        # Check if no other todo job are present for that position
        if not pos in [ j.pos for j in self.todo]:
            job = Job(task, pos)
            job.city_id = city_id
            self.todo.append(job)
            return True
        else:
            return False
    
    def jobReject(self, unit_id: str):
        """
        The rejected job is returned from inProgress to ToDo list 
        """
        if unit_id in self.inprogress:
            j = self.inprogress[unit_id]
            j.unit_id = ""  # clear unit_id
            j.subtask = 0
            if j.task in [Task.EXPLORE, Task.BUILD]:
                self.todo.append(j)
            del self.inprogress[unit_id]

    def count(self, task: str, pos: Position = None, city_id: str = "") -> int:
        """
        Return total number of active (not DONE) tasks with given parameters
        """
        retvalue = 0
        # check in self.todo 
        for job in self._activeJobs():
            if job.task == task:                
                if pos and pos != job.pos:
                    continue
                if city_id and city_id != job.city_id:
                    continue
                retvalue += 1
        return retvalue 

    def jobRequest(self, unit: Unit):
        """ 
        Unit can ask for a job, the function returns:
        - an 'inprogress' job for that unit_id if it's present
        - a new job from the 'todo' list
        """
        job = self.inprogress.get(unit.id)
        if job:
            return job
        # check for the first Job from the 'todo' list
        if unit.get_cargo_space_left() > 0:
            tile = self.parent.find_closest_resources(unit.pos)
            if not tile:
                job = Job(Task.SLEEP, unit.pos)
            else: 
                job = Job(Task.HARVEST, tile.pos)
            job.unit_id = unit.id
            self.inprogress[unit.id] = job
            return job
        else:
            job = self._nextJob(pos=unit.pos)
            if job:
                job.unit_id = unit.id
                job.subtask = 0
                self.inprogress[unit.id] = job
                return job
            else: # none to do -> SLEEP
                job = Job(Task.SLEEP, unit.pos)
                job.unit_id = unit.id
                self.inprogress[unit.id] = job
                return job
        
    def jobDone(self, unit_id):
        job = self.inprogress[unit_id]
        self.done.append(job)
        del self.inprogress[unit_id]


    def activeJobToPos(self, pos: Position) -> bool:
        return pos in [j.pos for j in self.inprogress.values()]

    def checkActiveJobs(self, units : List):
        """ 
        Using list of Units check if there are some InProgress Jobs assigned to 
        Unit no more on the list (dead unit). If the case then:
        - return Job to ToDos
        - add dead unit.id to rip List
        """
        morgue = []
        for unit_id in self.inprogress:
            if unit_id not in [u.id for u in units]:
                morgue.append(unit_id)
        for unit_id in morgue:
            # mov job to self.todo
            self.jobReject(unit_id)
            # add unit_id in self.rip
            self.rip.append(unit_id)

class GameExtended(Game):
    """ A Game class with steroids """

    def __init__(self):
        Game.__init__(self)
        self.job_board = JobBoard(self)
        self.resource_tiles = []

    def _update(self, messages):
        if messages["step"] == 0:
            Game._initialize(self, messages["updates"])
            Game._update(self, messages["updates"][2:])
            self.id = messages.player
        else:
            Game._update(self, messages["updates"])
        self.player = self.players[self.id]
        self.opponent = self.players[(self.id + 1) % 2]
        self.resource_tiles = self._free_resources()
        self.job_board.checkActiveJobs(self.player.units)

    def _free_resources(self):
        resource_tiles: list[Cell] = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                cell = self.map.get_cell(x, y)
                if cell.has_resource():
                    if cell.resource.type == Constants.RESOURCE_TYPES.COAL and not self.player.researched_coal():
                        continue
                    if cell.resource.type == Constants.RESOURCE_TYPES.URANIUM and not self.player.researched_uranium():
                        continue
                    # only resources without inprogress active tasks
                    if not self.job_board.activeJobToPos(cell.pos): 
                        resource_tiles.append(cell)
        return resource_tiles

    def find_closest_resources(self, pos, min_distance = 0):
        closest_dist = math.inf
        closest_resource_tile = None
        for resource_tile in self.resource_tiles:
            # we skip over resources that we can't mine due to not having researched them
            # if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not self.player.researched_coal():
            #    continue
            #if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not self.player.researched_uranium():
            #    continue
            dist = resource_tile.pos.distance_to(pos)
            if min_distance <= dist < closest_dist:
                closest_dist = dist
                closest_resource_tile = resource_tile
        return closest_resource_tile

    def find_closest_freespace(self, pos):
        open_list = [(pos.x, pos.y)]
        check_dirs = [
            DIRECTIONS.NORTH,
            DIRECTIONS.EAST,
            DIRECTIONS.SOUTH,
            DIRECTIONS.WEST
        ]
        while open_list:
            cur_pos = open_list.pop(0)
            cur_cell = self.map.get_cell(cur_pos[0], cur_pos[1])
            for direction in check_dirs:
                next_pos = cur_cell.pos.translate(direction, 1)
                if not 0 <= next_pos.x < self.map_width:
                    continue
                if not 0 <= next_pos.y < self.map_height:
                    continue
                next_cell = self.map.get_cell_by_pos(next_pos)
                if next_cell.citytile:
                    continue
                if next_cell.resource:
                    open_list.append((next_cell.pos.x, next_cell.pos.y))
                    continue
                return next_cell.pos
        return pos

    def path_to(self, from_pos: Position, to_pos: Position,  noCities=False, noResources=False) -> List[Tuple]:
        """ 
        Pathfinding : returns a direction of movement 
        -----
        Using the Dijkstra's algorithm
        """

        path: List[Tuple] = []
        spos = to_pos
        epos = from_pos
        open_list = [(spos.x, spos.y)]
        board = {(x, y): None for x in range(self.map_width)
                 for y in range(self.map_height)}

        board[(spos.x, spos.y)] = 0

        check_dirs = [
            DIRECTIONS.NORTH,
            DIRECTIONS.EAST,
            DIRECTIONS.SOUTH,
            DIRECTIONS.WEST
        ]

        while open_list:
            cur_pos = open_list.pop(0)
            cur_cell = self.map.get_cell(cur_pos[0], cur_pos[1])
            dist = board[(cur_cell.pos.x, cur_cell.pos.y)]
            if cur_cell.pos.is_adjacent(epos):
                board[(epos.x, epos.y)] = dist + 1
                break
            for direction in check_dirs:
                next_pos = cur_cell.pos.translate(direction, 1)
                if not 0 <= next_pos.x < self.map_width:
                    continue
                if not 0 <= next_pos.y < self.map_height:
                    continue
                next_cell = self.map.get_cell_by_pos(next_pos)
                if noCities and next_cell.citytile:
                    continue
                if noResources and next_cell.resource:
                    continue
                if next_cell.units:
                    continue
                if board[(next_cell.pos.x, next_cell.pos.y)] != None:
                    continue
                board[(next_cell.pos.x, next_cell.pos.y)] = dist + 1
                open_list.append((next_cell.pos.x, next_cell.pos.y))
        # return the path
        dist = board[(epos.x, epos.y)]
        if not dist:
            # no path founded
            return [DIRECTIONS.CENTER, []]
        cur_step = (DIRECTIONS.CENTER, epos.x, epos.y, dist)
        path.append(cur_step)
        dist -= 1
        while dist >= 0:
            for direction in check_dirs:
                cur_pos = Position(cur_step[1], cur_step[2])
                next_pos = cur_pos.translate(direction, 1)
                if not 0 <= next_pos.x < self.map_width:
                    continue
                if not 0 <= next_pos.y < self.map_height:
                    continue
                if board[(next_pos.x, next_pos.y)] == dist:
                    cur_step = (direction, next_pos.x, next_pos.y, dist)
                    path.append(cur_step)
                    dist -= 1
                    break

        if len(path) > 1:
            direction = path[1][0]
        else:
            direction = path[0][0]
        return [direction, path]
