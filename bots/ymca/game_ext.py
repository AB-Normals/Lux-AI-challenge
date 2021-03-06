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
    BUILD = "b"         # Build a citytile
    HARVEST = "h"       # Get resouce
    ENERGIZE = "e"      # Feed a city with resource


class Job:
    def __init__(self, task: str, pos: Position):
        self.pos: Position = pos
        self.task: str = task
        self.unit_id: str = ""


class JobBoard:
    """
    This is a Bulletin Board with 3 different lists:
    - todo : list of jobs no-one has in charge
    - inprogress : jobs currently in progress (with unit who has the assignement)
    - done : completed jobs (only for debug pouposes) 
    """

    def __init__(self, parent):
        self.todo: List = []
        self.inprogress: Dict = {}
        self.done: List = []
        self.parent = parent

    def _nextJob(self, pos: Position = None):
        # TODO: need a heuristics for job selection based on different parameters:
        #       as unit position, time of day, priority.
        #       Now no heurostics
        if self.todo:
            return self.todo.pop(0)
        else:
            # TODO: choose a default Job
            return None

    def add(self, task: str, pos: Position):
        # Check if no other todo job are present for that position
        if not pos in [ j.pos for j in self.todo]:
            job = Job(task, pos)
            self.todo.append(job)

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
            tile = self.parent._find_closest_resources(unit.pos)
            if not tile:
                job = Job(Task.SLEEP, unit.pos)
            else: 
                job = Job(Task.HARVEST, tile.pos)
            self.inprogress[unit.id] = job
            return job
        else:
            job = self._nextJob(pos=unit.pos)
            if job:
                job.unit_id = unit.id
                self.inprogress[unit.id] = job
                return job
            else: # none to do -> SLEEP
                job = Job(Task.SLEEP, unit.pos)
                self.inprogress[unit.id] = job
                return job

        
    def jobDone(self, unit_id):
        job = self.inprogress[unit_id]
        self.done.append(job)
        del self.inprogress[unit_id]


    def activeJobToPos(self, pos: Position) -> bool:
        return pos in [j.pos for j in self.inprogress.values()]

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

    def _free_resources(self):
        resource_tiles: list[Cell] = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                cell = self.map.get_cell(x, y)
                if cell.has_resource():
                    # only resources without inprogress active tasks
                    if not self.job_board.activeJobToPos(cell.pos): 
                        resource_tiles.append(cell)
        return resource_tiles

    def _find_closest_resources(self, pos):
        closest_dist = math.inf
        closest_resource_tile = None
        for resource_tile in self.resource_tiles:
            # we skip over resources that we can't mine due to not having researched them
            if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not self.player.researched_coal():
                continue
            if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not self.player.researched_uranium():
                continue
            dist = resource_tile.pos.distance_to(pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_resource_tile = resource_tile
        return closest_resource_tile


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
