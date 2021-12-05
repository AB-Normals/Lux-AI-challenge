import os
import math
import sys
from typing import List, Tuple

# for kaggle-environments
from abn.game_ext import GameExtended
from abn.jobs import Task, Job, JobBoard
from abn.actions import Actions
from lux.game_map import Position, Cell, RESOURCE_TYPES
from lux.game_objects import City
from lux.game_constants import GAME_CONSTANTS

from lux import annotate

## DEBUG ENABLE
DEBUG_SHOW_TIME = False
DEBUG_SHOW_CITY_JOBS = False
DEBUG_SHOW_CITY_FULLED = False
DEBUG_SHOW_EXPAND_MAP = True
DEBUG_SHOW_EXPAND_LIST = False
DEBUG_SHOW_INPROGRESS = True
DEBUG_SHOW_TODO = True
DEBUG_SHOW_ENERGY_MAP = False
DEBUG_SHOW_ENEMY_CITIES = False
DEBUG_SHOW_INVASION_MAP = False
DEBUG_SHOW_EXPLORE_MAP = False

MAX_CITY_SIZE = 10
DISTANCE_BETWEEN_CITIES = 5
        
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


def can_build_worker(player) -> int:
    # get nr of cytititles
    nr_cts = 0
    for k, c in player.cities.items():
        nr_cts += len(c.citytiles)
    return max(0, nr_cts - len(player.units))

def city_can_expand(city: City, jobs: JobBoard) -> bool:
    # City can expand if has fuel to pass the night 
    has_energy = city.isFulled()
    # City can expand to MAX_CITY_SIZE tiles
    can_expand = len(city.citytiles) + jobs.count(Task.BUILD, city_id=city.cityid) < MAX_CITY_SIZE
    return has_energy & can_expand

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
    if DEBUG_SHOW_TIME:
        actions.append(annotate.sidetext(f"Time : {game_state.time}"))
        actions.append(annotate.sidetext(f" {game_state.lux_time}h till night"))
        if game_state.isMorning() : dbg = "Morning"
        elif game_state.isEvening() : dbg = "Evening"
        elif game_state.isNight() : dbg = "Night"
        else: dbg = "Daytime"
        actions.append(annotate.sidetext(f"it is {dbg}"))
    
    #---------------------------------------------------------------------------------------------------------
    # Cities Management
    #---------------------------------------------------------------------------------------------------------
    for _, city in player.cities.items():
        city_size = len(city.citytiles)

        #--- EXPAND THE CITY ---
        if DEBUG_SHOW_EXPAND_LIST:
            exp_pos = game_state.expand_map.get(city.cityid)
            actions.append(annotate.sidetext(f"{city.cityid} expand in "))
            for x, y, v in exp_pos:
                actions.append(annotate.sidetext(f"  ({x}; {y}) {v}"))

        if city_can_expand(city, jobs) and city.isFulled():
            exp_pos = game_state.expand_map.get(city.cityid)
            if exp_pos:
                x, y, v = exp_pos[0]
                #if v:   # expand only if there is a resource nearby
                jobs.addJob(Task.BUILD, Position(x, y), city_id=city.cityid)
        #else:
        #    jobs.addJob(Task.INVASION, None, city_id=city.cityid)         

        #--- SPAWN WORKERS OR RESEARCH ---
        for ct in city.citytiles:
            pxy = ct.pos
            if DEBUG_SHOW_CITY_FULLED:
                actions.append(annotate.text(pxy.x, pxy.y, f"{city.isFulled()}"))
            if ct.can_act():
                if can_build_worker(player) - actions.new_workers > 0:
                    actions.build_worker(ct)
                    # actions.append(ct.build_worker())
                elif not player.researched_uranium():
                    actions.append(ct.research())
            if not city.isFulled(): # and not game_state.isNight():
                if jobs.count(Task.ENERGIZE, city_id=city.cityid) < (city_size + 1) // 2:
                    dbg = jobs.count(Task.ENERGIZE, city_id=city.cityid)
                    dbg2 = (city_size + 1) // 2
                    if DEBUG_SHOW_CITY_JOBS:
                        actions.append(annotate.sidetext(f"{city.cityid}: NRG {dbg} < {dbg2}"))
                    jobs.addJob(Task.ENERGIZE, ct.pos, city_id = city.cityid)                                     

    # Debug jobs.count
    if DEBUG_SHOW_CITY_JOBS:
        dbg = jobs.count(Task.BUILD, city_id=city.cityid)
        actions.append(annotate.sidetext(f"{city.cityid}: {dbg} BLD"))
        dbg = jobs.count(Task.ENERGIZE, city_id=city.cityid)
        actions.append(annotate.sidetext(f"{city.cityid}: {dbg} NRG"))
    #---------------------------------------------------------------------------------------------------------



    #---------------------------------------------------------------------------------------------------------
    # Units Management
    #---------------------------------------------------------------------------------------------------------
    if DEBUG_SHOW_INPROGRESS:
        actions.append(annotate.sidetext(f"[INPROGRESS]"))
    sorted_units = sorted(player.units, key=lambda u: u.cooldown, reverse=True)        
    for unit in sorted_units:
        
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker():
            my_job = jobs.jobRequest(unit)

            if not unit.can_act():
                actions.stay(unit)
                if DEBUG_SHOW_INPROGRESS:
                    actions.append(annotate.sidetext(f"!{my_job}"))
                continue
            else:
                if DEBUG_SHOW_INPROGRESS:
                    actions.append(annotate.sidetext(f">{my_job}"))

            # Check if is evening time, if so, to survive, every
            # job with risk of not having enough energy is dropped
            # and a new HARVEST job is taken.
#            if game_state.isNight():
#                if  (my_job.task == Task.BUILD and my_job.subtask > 0) or \
#                    (my_job.task == Task.EXPLORE and my_job.subtask > 0):
#                    actions.stay(unit)
#                    jobs.jobDrop(unit.id)
#                    continue    

            if my_job.task == Task.HARVEST:
                # if not in a city and in a cell with energy available stay here to harvest
                if  game_state.getEnergy(unit.pos.x, unit.pos.y) != 0 and \
                    not game_state.map.get_cell_by_pos(unit.pos).citytile: 
                        actions.stay(unit)  # stay in the same position
                else:   # find a new resource position
                    if unit.pos == my_job.pos:
                        tile = game_state.find_closest_resources(unit.pos)
                        if not tile:    # no more resources to harvest
                            actions.stay(unit)  # stay in the same position
                            jobs.jobDrop(unit.id)
                        else: # move to resource
                            my_job.pos = tile.pos
                    if unit.pos != my_job.pos:
                        move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                        if not actions.move(unit, move.direction): # cannot move to a resource tile
                                jobs.jobReject(unit.id)
                if unit.get_cargo_space_left() == 0:
                    actions.stay(unit)
                    jobs.jobDone(unit.id)

            elif my_job.task == Task.ENERGIZE:
                if my_job.subtask == 0: # search for resource
                    if game_state.getEnergy(my_job.pos.x, my_job.pos.y) != 0:
                        # citytile is adiacent to a resource so go directly there
                        my_job.subtask = 1
                    # If unit is in the citytile and can grab energy then job is done (unit stay there)
                    elif unit.energy >= 10 * unit.light_upkeep:
                        # citytile is adiacent to a resource so go directly there
                        my_job.subtask = 1
                    elif unit.get_cargo_space_left() == 0:
                        my_job.subtask = 1
                    elif (game_state.map.get_cell_by_pos(unit.pos).citytile or 
                        game_state.getEnergy(unit.pos.x, unit.pos.y) == 0 ):
                        tile = game_state.find_closest_resources(unit.pos)
                        if not tile:
                            actions.stay(unit)  # stay in the same position
                            jobs.jobReject(unit.id)
                        else: 
                            move = unit.pos.path_to(tile.pos, game_state.map, playerid=game_state.id)
                            if not actions.move(unit, move.direction): # cannot move to a resource tile
                                jobs.jobReject(unit.id)
                if my_job.subtask == 1: # go to citytile
                    if unit.pos == my_job.pos:
                        actions.stay(unit)  # stay in the same position
                        jobs.jobDone(unit.id)
                    else:                
                        move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                        if not actions.move(unit, move.direction):
                            jobs.jobReject(unit.id)

            elif my_job.task == Task.BUILD:
                if my_job.subtask == 0: # First need to full up unit
                    if unit.get_cargo_space_left() == 0:
                        my_job.subtask = 1
                    elif (game_state.map.get_cell_by_pos(unit.pos).citytile or 
                        game_state.getEnergy(unit.pos.x, unit.pos.y) == 0 ):
                        tile = game_state.find_closest_resources(unit.pos)
                        if not tile:    # no reacheable resource
                            actions.stay(unit)  # stay in the same position
                            jobs.jobDrop(unit.id)
                        else: 
                            move = unit.pos.path_to(tile.pos, game_state.map, playerid=game_state.id)
                            if not actions.move(unit, move.direction):
                                jobs.jobDrop(unit.id)
                if my_job.subtask == 1: # Go to Build position
                    if unit.pos == my_job.pos:
                        if unit.get_cargo_space_left() > 0:
                            actions.stay(unit)  # stay in the same position
                            jobs.jobDrop(unit.id)
                        else:
                            actions.build_city(unit)
                            my_job.subtask = 2
                    else:
                        move = unit.pos.path_to(my_job.pos, game_state.map, noCities=True)
                        if move.path:
                            if not actions.move(unit, move.direction):
                                jobs.jobDrop(unit.id)
                            # actions.append(unit.move(move_dir))
                            # Draw the path
                            actions.append(annotate.x(my_job.pos.x, my_job.pos.y))
                            for i in range(len(move.path)-1):
                                actions.append(annotate.line(
                                    move.path[i][1], move.path[i][2], 
                                    move.path[i+1][1], move.path[i+1][2]))                        
                        else:   # not path found
                            jobs.jobDone(unit.id)
                elif my_job.subtask == 2:
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
                    if not actions.move(unit, move_dir):
                        jobs.jobReject(unit.id)

            elif my_job.task == Task.EXPLORE:
                # this is a multistate task so my_job.subtask is the state
                if my_job.subtask == 0: # find the position of resource (min 4 step from city)
                    # get position of city that emitted the job
                    if my_job.city_id in player.cities:
                        pos = player.cities[my_job.city_id].citytiles[0].pos
                    else:
                        pos = my_job.pos
                    explore_pos = game_state.getClosestExploreTarget(pos, min_distance=DISTANCE_BETWEEN_CITIES)
                    if explore_pos:
                        my_job.subtask = 1  # HARVEST resource from position
                        my_job.pos = explore_pos
                    else:
                        jobs.jobDone(unit.id)

                if my_job.subtask == 1: # HARVEST resource from position
                    if unit.pos == my_job.pos:
                        if unit.get_cargo_space_left() > 0:
                            if not game_state.map.get_cell_by_pos(unit.pos).has_resource:
                                #jobs.jobReject(unit.id)
                                jobs.jobDrop(unit.id)
                        else: # next subtask
                            my_job.pos = game_state.find_closest_freespace(unit.pos)
                            my_job.subtask = 2  # BUILD A NEW CITY
                    else:
                        # move_dir = unit.pos.direction_to(my_job.pos)
                        move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                        if not actions.move(unit, move.direction):
                            # jobs.jobReject(unit.id)
                            jobs.jobDrop(unit.id)
                if my_job.subtask == 2: # BUILD A NEW CITY
                    if unit.pos == my_job.pos:
                        # TODO: need to wait until next day
                        actions.build_city(unit)
                        my_job.subtask = 3 # WAIT UNTIL NEXT DAY
                    else:
                        #move_dir = unit.pos.direction_to(my_job.pos)
                        move = unit.pos.path_to(my_job.pos, game_state.map, noCities=True, playerid=game_state.id)
                        if not actions.move(unit, move.direction):
                            action = unit.build_city()
                            # jobs.jobReject(unit.id) 
                            jobs.jobDrop(unit.id)   
                if my_job.subtask == 3: # Now feed that city
                    my_job.task = Task.ENERGIZE
                    my_job.subtask = 0
                    actions.stay(unit)

            elif my_job.task == Task.INVASION:
                if my_job.subtask == 0: 
                    # get an invasion target position
                    target_pos = game_state.getClosestInvasionTarget(unit.pos)                    
                    if not target_pos:
                        actions.stay(unit)
                        jobs.jobDone(unit.id)
                        continue
                    my_job.data["target"] = target_pos
                    if unit.get_cargo_space_left() == 0:    # if unit is full
                        my_job.pos = target_pos
                        my_job.subtask = 2
                    else:
                        # find a resource in the halfway to the target
                        res_cell = game_state.find_closest_resources(unit.pos.halfway(target_pos))
                        if res_cell:
                            my_job.subtask = 1  # HARVEST resource from position
                            my_job.pos = res_cell.pos
                        else:
                            actions.stay(unit)
                            jobs.jobDone(unit.id)
                            continue
                if my_job.subtask == 1: # HARVEST resource from position
                    if unit.pos == my_job.pos:
                        if unit.get_cargo_space_left() == 0:
                            my_job.pos = my_job.data["target"]
                            my_job.subtask = 2  # BUILD A NEW CITY
                        elif not game_state.getEnergy(unit.pos.x, unit.pos.y) > 0:
                            res_cell = game_state.find_closest_resources(unit.pos)
                            if res_cell:
                                my_job.pos = res_cell.pos
                            else:
                                actions.stay(unit)
                                jobs.jobDone(unit.id)
                                continue
                        else: # next subtask
                            actions.stay(unit)  # stay untill cargo is fulled
                    else:
                        # move_dir = unit.pos.direction_to(my_job.pos)
                        move = unit.pos.path_to(my_job.pos, game_state.map, playerid=game_state.id)
                        if not actions.move(unit, move.direction):  # no way to move
                            jobs.jobDrop(unit.id)
                if my_job.subtask == 2: # BUILD A NEW CITY
                    if unit.pos == my_job.pos:
                        actions.build_city(unit)
                        jobs.jobDone(unit.id)
                    else:
                        move = unit.pos.path_to(my_job.pos, game_state.map, noCities=True, playerid=game_state.id)
                        if not actions.move(unit, move.direction):
                            if unit.get_cargo_space_left() == 0 and not game_state.map.get_cell_by_pos(unit.pos).has_resource:
                                actions.build_city(unit)
                                jobs.jobDone(unit.id)
                            else:
                                actions.stay(unit)


    ## Debug Text
    if DEBUG_SHOW_TODO:
        actions.append(annotate.sidetext(f"[TODO] {len(jobs.todo)}"))
        for task in jobs.todo:
            actions.append(annotate.sidetext(task))
    #--------------------------------------------------------------------------------------------------------    

    # Debug "show expand map"
    if DEBUG_SHOW_EXPAND_MAP:
        for x, y, e in [ p for a in game_state.expand_map.values() for p in a]:
            actions.append(annotate.circle(x, y))
            actions.append(annotate.text(x, y, e))

    ## Debug "show energy map"
    if DEBUG_SHOW_ENERGY_MAP:
        for (x, y),v in game_state.energy_map.items():
            actions.append(annotate.text(x, y, v))

    ## Debug "show enemy map"
    if DEBUG_SHOW_ENEMY_CITIES:
        for x, y in game_state.enemy_map:
            actions.append(annotate.circle(x, y))

    ## Debug "show invasion map"
    if DEBUG_SHOW_INVASION_MAP:
        for x, y in game_state.invasion_map:
            actions.append(annotate.x(x, y))

    ## Debug "show explore map"
    if DEBUG_SHOW_EXPLORE_MAP:
        for x, y in game_state.explore_map:
            actions.append(annotate.x(x, y))

#    actions.append(annotate.sidetext(f"[INPROGRESS] {len(jobs.inprogress)}"))
#    for task in jobs.inprogress:
#        actions.append(annotate.sidetext(jobs.inprogress[task]))
    
#    actions.append(annotate.sidetext("-[CEMETERY]-"))
#    for uid in jobs.rip:
#        actions.append(annotate.sidetext(uid))

    return actions.actions
