import os
import math
import sys
from typing import List, Tuple

# for kaggle-environments
from game_ext import GameExtended, Task, Job, JobBoard
from lux.game_map import Position
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux.game_objects import Unit
from lux import annotate

# Define helper functions

class Actions:

    def __init__(self, game_state: GameExtended):
        self.game = game_state
        self.actions = [] 
        self.collisions = []

    def append(self, cmd: str):
        self.actions.append(cmd)
    
    def move(self, unit: Unit, dir):
        pos = unit.pos.translate(dir, 1)            
        if self._isPosOk(pos):
            self.collisions.append(pos)
            self.actions.append(unit.move(dir))
        else: # not move (direction = center)
            self.collisions.append(unit.pos)
            self.actions.append(unit.move(Constants.DIRECTIONS.CENTER))

    def _isPosOk(self, pos: Position) -> bool:
        if not 0 <= pos.x < self.game.map_width:
            return False
        if not 0 <= pos.y < self.game.map_height:
            return False
        if pos in self.collisions:
            return False
        return True

def find_closest_city_tile(pos, player):
    closest_city_tile = None
    if len(player.cities) > 0:
        closest_dist = math.inf
        # the cities are stored as a dictionary mapping city id to the city object, which has a citytiles field that
        # contains the information of all citytiles in that city
        for k, city in player.cities.items():
            for city_tile in city.citytiles:
                dist = city_tile.pos.distance_to(pos)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_city_tile = city_tile
    return closest_city_tile


def can_build_worker(player) -> bool:
    # get nr of cytititles
    nr_cts = 0
    for k, c in player.cities.items():
        nr_cts += len(c.citytiles)
    return nr_cts > len(player.units)


# Define global variables
game_state = GameExtended()
lets_build_city = False
build_pos = None
jobs = game_state.job_board


def agent(observation, configuration, DEBUG=False):
    global game_state
    global lets_build_city
    global build_pos
    max_city_size = 3

    ### Do not edit ###
    game_state._update(observation)
    actions = Actions(game_state)
    path: List[Tuple] = []


    ### AI Code goes down here! ###
    player = game_state.player
    opponent = game_state.opponent
    width, height = game_state.map.width, game_state.map.height

    for k, city in player.cities.items():
        # get energy cost for the night to come
        cost = 10 * len(city.citytiles) * city.get_light_upkeep()
        fulled = city.fuel > cost
        city_size = len(city.citytiles)
        city_can_expand = city_size < max_city_size
        more_space = fulled and city_can_expand
        for ct in city.citytiles:
            pxy = ct.pos
            actions.append(annotate.text(pxy.x, pxy.y, f"{fulled}"))
            if ct.can_act():
                if can_build_worker(player):
                    actions.append(ct.build_worker())
                else:
                    actions.append(ct.research())
            if not fulled:
                jobs.add(Task.ENERGIZE, ct.pos)  
            if fulled and city_can_expand:
                # choose a place to create a new citytile in same city
                for x, y in [(pxy.x, pxy.y+1), (pxy.x, pxy.y-1), (pxy.x+1, pxy.y), (pxy.x-1, pxy.y)]:
                    if not 0 <= x < game_state.map_width:
                        continue
                    if not 0 <= y < game_state.map_height:
                        continue
                    
                    cell = game_state.map.get_cell(x, y)
                    # actions.append(annotate.text(x, y, f"{x},{y}"))

                    if cell.citytile:
                        continue
                    if cell.has_resource():
                        continue
                    else:
                        actions.append(annotate.x(x, y))
                        jobs.add(Task.BUILD, Position(x, y))
                        no_more_space = False
                        break
        if fulled and no_more_space:
            job.add(Task.EXPLORE, None)
        

    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            my_job = jobs.jobRequest(unit)

            if my_job.task == Task.HARVEST:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    move_dir = unit.pos.direction_to(my_job.pos)
                    actions.move(unit, move_dir)
                    # action = unit.move(unit.pos.direction_to(
                    #    my_job.pos))
                    # actions.append(action)


            elif my_job.task == Task.ENERGIZE:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    move_dir = unit.pos.direction_to(my_job.pos)
                    actions.move(unit, move_dir)
                    # action = unit.move(unit.pos.direction_to(
                    #     my_job.pos))
                    # actions.append(action)

            elif my_job.task == Task.BUILD:
                if unit.pos == my_job.pos:
                    action = unit.build_city()
                    actions.append(action)
                    jobs.jobDone(unit.id)
                else:
                    move_dir, path = game_state.path_to(
                        unit.pos, my_job.pos, noCities=True)
                    if path:
                        actions.move(unit, move_dir)
                        # actions.append(unit.move(move_dir))
                        # Draw the path
                        for i in range(len(path)-1):
                            actions.append(annotate.line(
                                path[i][1], path[i][2], path[i+1][1], path[i+1][2]))
                    else:   # not path found
                        jobs.jobDone(unit.id)


            elif my_job.task == Task.SLEEP:
                if unit.pos == my_job.pos:
                    # TODO: need to wait until next day
                    jobs.jobDone(unit.id)
                else:
                    move_dir = unit.pos.direction_to(my_job.pos)
                    actions.move(unit, move_dir)

            elif my_job.task == Task.EXPLORE:
                if unit.pos == my_job.pos:
                    # TODO: need to wait until next day
                    jobs.jobDone(unit.id)
                else:
                    move_dir = unit.pos.direction_to(my_job.pos)
                    actions.move(unit, move_dir)


    return actions.actions
