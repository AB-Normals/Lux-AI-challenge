import math
from typing import List, Tuple

from .constants import Constants

DIRECTIONS = Constants.DIRECTIONS
RESOURCE_TYPES = Constants.RESOURCE_TYPES

class Movement:
    def __init__(self, direction, path):
        self.direction = direction
        self.path = path

class Resource:
    def __init__(self, r_type: str, amount: int):
        self.type = r_type
        self.amount = amount

class Cell:
    def __init__(self, x, y):
        self.pos = Position(x, y)
        self.resource: Resource = None
        self.citytile = None
        self.road = 0
        self.units = []
    def has_resource(self):
        return self.resource is not None and self.resource.amount > 0


class GameMap:
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.map: List[List[Cell]] = [None] * height
        for y in range(0, self.height):
            self.map[y] = [None] * width
            for x in range(0, self.width):
                self.map[y][x] = Cell(x, y)

    def get_cell_by_pos(self, pos) -> Cell:
        return self.map[pos.y][pos.x]

    def get_cell(self, x, y) -> Cell:
        return self.map[y][x]

    def _setResource(self, r_type, x, y, amount):
        """
        do not use this function, this is for internal tracking of state
        """
        cell = self.get_cell(x, y)
        cell.resource = Resource(r_type, amount)


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __sub__(self, pos) -> int:
        return abs(pos.x - self.x) + abs(pos.y - self.y)

    def __eq__(self, pos) -> bool:
        return self.x == pos.x and self.y == pos.y

    def __str__(self) -> str:
        return f"({self.x}; {self.y})"

    def distance_to(self, pos):
        """
        Returns Manhattan (L1/grid) distance to pos
        """
        return self - pos

    def is_adjacent(self, pos):
        return (self - pos) <= 1

    def equals(self, pos):
        return self == pos

    def translate(self, direction, units) -> 'Position':
        if direction == DIRECTIONS.NORTH:
            return Position(self.x, self.y - units)
        elif direction == DIRECTIONS.EAST:
            return Position(self.x + units, self.y)
        elif direction == DIRECTIONS.SOUTH:
            return Position(self.x, self.y + units)
        elif direction == DIRECTIONS.WEST:
            return Position(self.x - units, self.y)
        elif direction == DIRECTIONS.CENTER:
            return Position(self.x, self.y)

    def halfway(self, target_pos: 'Position') -> 'Position':
        """
        Return position in between this and target_pos
        """
        return Position((self.x + target_pos.x) // 2, (self.y + target_pos.y) // 2)

    def direction_to(self, target_pos: 'Position') -> DIRECTIONS:
        """
        Return closest position to target_pos from this position
        """
        check_dirs = [
            DIRECTIONS.NORTH,
            DIRECTIONS.EAST,
            DIRECTIONS.SOUTH,
            DIRECTIONS.WEST,
        ]
        closest_dist = self.distance_to(target_pos)
        closest_dir = DIRECTIONS.CENTER
        for direction in check_dirs:
            newpos = self.translate(direction, 1)
            dist = target_pos.distance_to(newpos)
            if dist < closest_dist:
                closest_dir = direction
                closest_dist = dist
        return closest_dir

    def path_to(self, target_pos: 'Position', map: GameMap, noCities=False, noResources=False, playerid = None) -> DIRECTIONS:
        """ 
        Pathfinding : returns a direction of movement 
        -----
        Using the Dijkstra's algorithm
        """

        check_dirs = [
            DIRECTIONS.NORTH,
            DIRECTIONS.EAST,
            DIRECTIONS.SOUTH,
            DIRECTIONS.WEST
        ]

        path: List[Tuple] = []
        spos = target_pos
        epos = self
        open_list = [(spos.x, spos.y)]
        board = {(x, y): None for x in range(map.width)
                for y in range(map.height)}

        board[(spos.x, spos.y)] = 0

        while open_list:
            cur_pos = open_list.pop(0)
            cur_cell = map.get_cell(cur_pos[0], cur_pos[1])
            dist = board[(cur_cell.pos.x, cur_cell.pos.y)]
            if cur_cell.pos.is_adjacent(epos):
                board[(epos.x, epos.y)] = dist + 1
                break
            for direction in check_dirs:
                next_pos = cur_cell.pos.translate(direction, 1)
                if not 0 <= next_pos.x < map.width:
                    continue
                if not 0 <= next_pos.y < map.height:
                    continue
                next_cell = map.get_cell_by_pos(next_pos)
                # check if CityTile
                ct = next_cell.citytile
                if ct and (noCities or not ct.team == playerid):
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
            return Movement(DIRECTIONS.CENTER, [])
        cur_step = (DIRECTIONS.CENTER, epos.x, epos.y, dist)
        path.append(cur_step)
        dist -= 1
        while dist >= 0:
            for direction in check_dirs:
                cur_pos = Position(cur_step[1], cur_step[2])
                next_pos = cur_pos.translate(direction, 1)
                if not 0 <= next_pos.x < map.width:
                    continue
                if not 0 <= next_pos.y < map.height:
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
        return Movement(direction, path)
