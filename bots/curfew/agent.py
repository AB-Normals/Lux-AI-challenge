import os
import math
import sys
from typing import List, Tuple

# for kaggle-environments
from abn.game_ext import GameExtended
from abn.jobs import Task, Job, JobBoard
from abn.actions import Actions
from lux.game_map import Position
from lux.game_map import Cell, RESOURCE_TYPES
from lux.game_constants import GAME_CONSTANTS

from lux import annotate

MAX_CITY_SIZE = 5
DISTANCE_BETWEEN_CITIES = 3

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
actions = Actions(game_state)
lets_build_city = False
build_pos = None
jobs = game_state.job_board
completed_cities = []

def agent(observation, configuration, DEBUG=False):
    global game_state
    global actions
    global lets_build_city
    global build_pos
    global completed_cities


    ### Do not edit ###
    game_state._update(observation)
    actions.update()
    path: List[Tuple] = []

    ### AI Code goes down here! ###
    player = game_state.player
    opponent = game_state.opponent
    # width, height = game_state.map.width, game_state.map.height
    actions.append(annotate.sidetext(f"Time : {game_state.time}"))
    actions.append(annotate.sidetext(f" {game_state.lux_time}h till night"))

    for _, city in player.cities.items():
        # get energy cost for the night to come
        cost = 10 * len(city.citytiles) * city.get_light_upkeep()
        fulled = city.fuel > cost
        city_size = len(city.citytiles)
        # city can expand if actual city size + requested build is less than maximum size
        # city_can_expand = city.cityid not in completed_cities
        city_can_expand = city_size + jobs.count(Task.BUILD, city_id=city.cityid) < MAX_CITY_SIZE
        if not city_can_expand and fulled:
            if city_size + jobs.count(Task.BUILD, city_id=city.cityid) >= MAX_CITY_SIZE:
                # completed_cities.append(city.cityid)
                jobs.addJob(Task.EXPLORE, Position(-1,-1), city_id= city.cityid)
                city_can_expand = False
        #more_space = fulled and city_can_expand
        for ct in city.citytiles:
            pxy = ct.pos
            actions.append(annotate.text(pxy.x, pxy.y, f"{fulled}"))
            if ct.can_act():
                if can_build_worker(player):
                    actions.append(ct.build_worker())
                else:
                    actions.append(ct.research())
            if not fulled:
                if jobs.count(Task.ENERGIZE, city_id=city.cityid) < (MAX_CITY_SIZE + 1) // 2:
                    jobs.addJob(Task.ENERGIZE, ct.pos, city_id = city.cityid)              
        if fulled and city_can_expand:
            build_requested = False
            pxy = Position(0,0)
            for ct in city.citytiles:
                pxy = ct.pos
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
                    if jobs.activeJobToPos(cell.pos):
                        build_requested = True
                        continue
                    else:
                        # actions.append(annotate.x(x, y))
                        jobs.addJob(Task.BUILD, Position(x, y), city_id=city.cityid)
                        build_requested = True
                        break
                if build_requested:
                    break
            if not build_requested: # City can not expand
                completed_cities.append(city.cityid)
                jobs.addJob(Task.EXPLORE, Position(-1,-1), city_id= city.cityid)
        
    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            my_job = jobs.jobRequest(unit)
            
            if my_job.task == Task.HARVEST:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                    # move_dir = unit.pos.direction_to(my_job.pos)
                    if not actions.move(unit, move.direction):
                        jobs.jobReject(unit.id)

            elif my_job.task == Task.ENERGIZE:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    #move_dir = unit.pos.direction_to(my_job.pos)
                    move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                    actions.move(unit, move.direction)
                    # action = unit.move(unit.pos.direction_to(
                    #     my_job.pos))
                    # actions.append(action)

            elif my_job.task == Task.BUILD:
                if my_job.subtask == 0:
                    if unit.pos == my_job.pos:
                        if unit.get_cargo_space_left() > 0:
                            jobs.jobReject(unit.id)
                        else:
                            action = unit.build_city()
                            actions.append(action)
                            my_job.subtask = 1
                    else:
                        move = unit.pos.path_to(my_job.pos, game_state.map, noCities=True)
                        if move.path:
                            actions.move(unit, move.direction)
                        # actions.append(unit.move(move_dir))
                        # Draw the path
                        actions.append(annotate.x(my_job.pos.x, my_job.pos.y))
                        for i in range(len(path)-1):
                            actions.append(annotate.line(
                                path[i][1], path[i][2], path[i+1][1], path[i+1][2]))
                        
                        else:   # not path found
                            jobs.jobDone(unit.id)
                if my_job.subtask == 1:
                    # if city has adiacent energy then Unit Stay until new day
                    if game_state.getEnergy(unit.pos.x, unit.pos.y) > 0:
                        if game_state.time >= 39:
                            jobs.jobDone(unit.id)
                    else:
                        jobs.jobDone(unit.id)

            elif my_job.task == Task.SLEEP:
                if unit.pos == my_job.pos:
                    if game_state.time >= 39:
                        jobs.jobDone(unit.id)
                else:
                    move_dir = unit.pos.direction_to(my_job.pos)
                    actions.move(unit, move_dir)

            elif my_job.task == Task.EXPLORE:
                # this is a multistate task so my_job.subtask is the state
                if my_job.subtask == 0: # find the position of resource (min 4 step from city)
                    # get position of city that emitted the job
                    if my_job.city_id in player.cities:
                        pos = player.cities[my_job.city_id].citytiles[0].pos
                        res_cell = game_state.find_closest_resources(pos, min_distance=DISTANCE_BETWEEN_CITIES)
                        if res_cell:
                            my_job.subtask = 1  # HARVEST resource from position
                            my_job.pos = res_cell.pos
                        else:
                            jobs.jobDone(unit.id)
                    else:
                        jobs.jobDone(unit.id)
                if my_job.subtask == 1: # HARVEST resource from position
                    if unit.pos == my_job.pos:
                        if unit.get_cargo_space_left() > 0:
                            if not game_state.map.get_cell_by_pos(unit.pos).has_resource:
                                jobs.jobReject(unit.id)
                        else: # next subtask
                            my_job.pos = game_state.find_closest_freespace(unit.pos)
                            my_job.subtask = 2  # BUILD A NEW CITY
                    else:
                        # move_dir = unit.pos.direction_to(my_job.pos)
                        move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                        actions.move(unit, move.direction)
                if my_job.subtask == 2: # BUILD A NEW CITY
                    if unit.pos == my_job.pos:
                        # TODO: need to wait until next day
                        action = unit.build_city()
                        actions.append(action)
                        my_job.subtask = 3 # WAIT UNTIL NEXT DAY
                    else:
                        #move_dir = unit.pos.direction_to(my_job.pos)
                        move = unit.pos.path_to(my_job.pos, game_state.map, noCities=True, playerid=game_state.id)
                        actions.move(unit, move.direction)    
                if my_job.subtask == 3: # WAIT UNTIL NEXT DAY
                    if game_state.getEnergy(unit.pos.x, unit.pos.y) > 0:
                        if game_state.time >= 39:
                            jobs.jobDone(unit.id)
                    else:
                        jobs.jobDone(unit.id)

    ## Debug Text
    actions.append(annotate.sidetext("----[TODO]----"))
    for task in jobs.todo:
        actions.append(annotate.sidetext(task))

    actions.append(annotate.sidetext("-[INPROGRESS]-"))
    for task in jobs.inprogress.values():
        actions.append(annotate.sidetext(task))
    

    return actions.actions
