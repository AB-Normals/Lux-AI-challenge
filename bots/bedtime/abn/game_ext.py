# GameExtended
# ---
# The Game class with steroids

import math
import weakref
from typing import Tuple, List, Dict

from abn.jobs import JobBoard

from lux.game import Game
from lux.game_map import Position, Cell
from lux.constants import Constants
from lux.game_objects import Unit

DIRECTIONS = Constants.DIRECTIONS
RESOURCE_TYPES = Constants.RESOURCE_TYPES

EVENING_HOURS = 10    # evening duration (end of day before night)
MORNING_HOURS = 10    # morning duration (start of day after night) 


class GameExtended(Game):
    """ A Game class with steroids """

    def __init__(self):
        Game.__init__(self)
        self.job_board = JobBoard(self)
        #self.resource_tiles = []
        self.energy_map = {}    # used to store data like a matrix using (x,y) as keys

    def _update(self, messages):
        if messages["step"] == 0:
            Game._initialize(self, messages["updates"])
            Game._update(self, messages["updates"][2:])
            self.id = messages.player
        else:
            Game._update(self, messages["updates"])
        self.player = self.players[self.id]
        self.opponent = self.players[(self.id + 1) % 2]
        #self.resource_tiles = self._free_resources()
        self.job_board.checkActiveJobs(self.player.units)
        self.time = self.turn % 40
        self.lux_time = max( 0 , 29 - self.time)
        self._build_energy_map()

    def isEvening(self):
        return (0 < self.lux_time <= EVENING_HOURS)

    def isMorning(self):
        return (self.time < MORNING_HOURS)
    
    def isNight(self):
        return (self.lux_time < 1)

    def _build_energy_map(self):
        for x in range(self.map_width):
            for y in range(self.map_height):
                self.energy_map[x,y] = self.getEnergy(x,y)

    def getEnergy(self, px, py) -> int:
        energy = 0
        # get energy from the cell
        for x, y in [(px, py), (px-1, py), (px, py-1), (px+1, py), (px, py+1)]:
            if not 0 <= x < self.map_width:
                continue
            if not 0 <= y < self.map_height:
                continue
            cell = self.map.get_cell(x, y)
            if cell.has_resource():
                if cell.resource.type == Constants.RESOURCE_TYPES.COAL and self.player.researched_coal():
                    energy += cell.resource.amount * Constants.RESOURCE_TO_FUEL_RATE.COAL
                if cell.resource.type == Constants.RESOURCE_TYPES.URANIUM and self.player.researched_uranium():
                    energy += cell.resource.amount * Constants.RESOURCE_TO_FUEL_RATE.URANIUM
                if cell.resource.type == Constants.RESOURCE_TYPES.WOOD:
                    energy += cell.resource.amount * Constants.RESOURCE_TO_FUEL_RATE.WOOD
        return energy
                    
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
        resource_tiles = self._free_resources()
        closest_dist = math.inf
        closest_resource_tile = None
        for resource_tile in resource_tiles:
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
