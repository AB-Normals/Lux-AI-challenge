from abn.game_ext import GameExtended
from lux.game_objects import Unit
from lux.game_map import Position
from lux.constants import Constants


class Actions:

    def __init__(self, game_state: GameExtended):
        self.game = game_state
        self.actions = [] 
        self.next_pos = {}  # Dictionary (unit.id: pos)
        self.req_pos = {}   # last requested position
        self.collision = []
    
    def update(self):
        """ need to call 'update' each turn """
        self.actions = []
        self.req_pos = self.next_pos.copy()
        self.next_pos = {}
        self.collision = []


    def append(self, cmd: str):
        self.actions.append(cmd)
    
    def move(self, unit: Unit, dir) -> bool:
        pos = unit.pos.translate(dir, 1)            
        if self._isPosOk(pos, unit):
            self.next_pos[unit.id] = pos
            self.actions.append(unit.move(dir))
            return True
        dir = self._alternativeDirection(dir)
        pos = unit.pos.translate(dir, 1)
        if self._isPosOk(pos, unit):
            self.next_pos[unit.id] = pos
            self.actions.append(unit.move(dir))
            return True
        else:
            self.next_pos[unit.id] = unit.pos
            return False

    def collided(self, unit: Unit) -> bool:
        return unit.id in self.collision

    def isReqPos(self, unit: Unit) -> bool:
        return self.req_pos[unit.id] == unit.pos

    def _isPosOk(self, pos: Position, unit: Unit) -> bool:
        if not 0 <= pos.x < self.game.map_width:
            return False
        if not 0 <= pos.y < self.game.map_height:
            return False
        if pos in self.next_pos.values():
            return False
        if unit.id in self.req_pos:     
            if self.req_pos[unit.id] == pos: # have a collision 
                self.collision.append(unit.id)
                return False
        return True

    def _alternativeDirection(self, dir):
        alternative= {
            Constants.DIRECTIONS.NORTH: Constants.DIRECTIONS.EAST,
            Constants.DIRECTIONS.EAST: Constants.DIRECTIONS.SOUTH,
            Constants.DIRECTIONS.SOUTH: Constants.DIRECTIONS.WEST,
            Constants.DIRECTIONS.WEST: Constants.DIRECTIONS.NORTH,
            Constants.DIRECTIONS.CENTER: Constants.DIRECTIONS.CENTER
        }
        return alternative[dir]