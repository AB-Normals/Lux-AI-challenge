# GameExtended
# ---
# The Game class with steroids

from typing import Tuple, List

from lux.game import Game
from lux.game_map import Position
from lux.constants import Constants


DIRECTIONS = Constants.DIRECTIONS
RESOURCE_TYPES = Constants.RESOURCE_TYPES


class GameExtended(Game):
    """ A Game class with steroids """

    def __init__(self):
        Game.__init__(self)

    def _update(self, messages):
        if messages["step"] == 0:
            Game._initialize(self, messages["updates"])
            Game._update(self, messages["updates"][2:])
            self.id = messages.player
        else:
            Game._update(self, messages["updates"])
        self.player = self.players[self.id]
        self.opponent = self.players[(self.id + 1) % 2]

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
        
        if len(path) > 1: direction = path[1][0]
        else: direction = path[0][0]
        return [direction, path]
