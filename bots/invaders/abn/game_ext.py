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
NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

class GameExtended(Game):
    """ A Game class with steroids """

    def __init__(self):
        Game.__init__(self)
        self.time = 0
        self.lux_time = 0
        self.job_board = JobBoard(self)
        #self.resource_tiles = []
        self.energy_map = {}    # energy value a unit can draw for each cell
        self.explore_map = {}   # position in near a resource where to explore and build city
        self.enemy_map = {}     # position of enemy citytiles
        self.invasion_map = {}  # map of cell adjacent to enemy citytiles
        self.expand_map = {}    # for each player city a list of adjacent cells and energy useable to expand
                                # ex: { "city.id": [(x,y,energy), (x,y,energy), ...] }
    

    def _update(self, messages):
        if messages["step"] == 0:
            Game._initialize(self, messages["updates"])
            Game._update(self, messages["updates"][2:])
            # self.id = messages.player
        else:
            Game._update(self, messages["updates"])
        self.player = self.players[self.id]
        self.opponent = self.players[(self.id + 1) % 2]
        #self.resource_tiles = self._free_resources()
        self.job_board.checkActiveJobs(self.player.units, self.player.cities)
        self.time = self.turn % 40
        self.lux_time = max( 0 , 29 - self.time)
        self._build_energy_map() # fill also the explore_map
        self._build_enemy_map()
        self._build_invasion_map()
        self._build_expand_map()

    def isEvening(self):
        return (0 < self.lux_time <= EVENING_HOURS)

    def isMorning(self):
        return (self.time < MORNING_HOURS)
    
    def isNight(self):
        return (self.lux_time < 1)

    def _build_energy_map(self):
        for x in range(self.map_width):
            for y in range(self.map_height):
                energy = self._getEnergy(x, y)
                self.energy_map[x,y] = energy
                if energy and not self.map.get_cell(x, y).has_resource() and not self.map.get_cell(x, y).citytile:
                    self.explore_map[x,y] = 1
    
    def _build_enemy_map(self):
        self.enemy_map = {}
        for x in range(self.map_width):
            for y in range(self.map_height):
                ct = self.map.get_cell(x, y).citytile
                if ct and ct.team != self.id:
                    self.enemy_map[x,y] = 1

    # build a map of all neighboring cells of enemy_map
    def _build_invasion_map(self):
        self.invasion_map = {} 
        for x, y in self.enemy_map:
            for dx, dy in NEIGHBORS:
                if 0 <= x + dx < self.map_width and 0 <= y + dy < self.map_height:
                    if not self.map.get_cell(x + dx, y + dy).citytile:
                        self.invasion_map[x + dx, y + dy] = 1

    def _build_expand_map(self):
        self.expand_map = {}
        for id, city in self.player.cities.items():
            self.expand_map[id] = []
            for ct in city.citytiles:
                for dx, dy in NEIGHBORS:
                    x = ct.pos.x + dx
                    y = ct.pos.y + dy
                    if 0 <= x < self.map_width and 0 <= y < self.map_height:
                        if not self.map.get_cell(x, y).citytile and \
                            not self.map.get_cell(x, y).has_resource():
                            self.expand_map[id].append((x, y, self.getEnergy(x,y)))
            self.expand_map[id].sort(key=lambda x: x[2], reverse=True)   

    def getClosestInvasionTarget(self, pos: Position) -> Position:
        """
        Returns the closest invasion target position
        """
        closest_invasion = None
        closest_distance = math.inf
        for x, y in self.invasion_map:
            distance = pos.distance_to(Position(x, y))
            if distance < closest_distance:
                closest_distance = distance
                closest_invasion = Position(x, y)
        return closest_invasion

    def getClosestExploreTarget(self, pos: Position, min_distance = 0) -> Position:
        """
        Returns the closest explore target position
        """
        closest_explore = None
        closest_distance = math.inf
        for x, y in self.explore_map:
            distance = pos.distance_to(Position(x, y))
            if min_distance <= distance < closest_distance:
                closest_distance = distance
                closest_explore = Position(x, y)
        return closest_explore

    def getEnergy(self, x, y) -> int:
        return self.energy_map[x,y]

    def _getEnergy(self, px, py) -> int:
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
            x, y = cur_pos
            if  not self.map.get_cell(x, y).citytile and \
                not self.map.get_cell(x, y).has_resource():
                return Position(x, y)

            # cur_cell = self.map.get_cell(cur_pos[0], cur_pos[1])
            for dx, dy in NEIGHBORS:
                if 0 <= x+dx < self.map_width and 0 <= y+dy < self.map_height:
                    open_list.append((x + dx, y + dy))
        return pos