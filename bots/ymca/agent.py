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
from lux import annotate

# Define helper functions

# the next snippet finds the closest resources that we can mine given position on a map


# def find_closest_resources(pos, player, resource_tiles):
#     closest_dist = math.inf
#     closest_resource_tile = None
#     for resource_tile in resource_tiles:
#         # we skip over resources that we can't mine due to not having researched them
#         if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal():
#             continue
#         if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium():
#             continue
#         dist = resource_tile.pos.distance_to(pos)
#         if dist < closest_dist:
#             closest_dist = dist
#             closest_resource_tile = resource_tile
#     return closest_resource_tile


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
    max_tiles = 1

    ### Do not edit ###
    game_state._update(observation)
    actions = []
    path: List[Tuple] = []

    ### AI Code goes down here! ###
    player = game_state.player
    opponent = game_state.opponent
    width, height = game_state.map.width, game_state.map.height

    for k, city in player.cities.items():
        # get energy cost for the night to come
        cost = 10 * len(city.citytiles) * city.get_light_upkeep()
        fulled = city.fuel > cost
        for ct in city.citytiles:
            pxy = ct.pos
            actions.append(annotate.text(pxy.x, pxy.y, f"{fulled}"))
            if ct.can_act():
                if can_build_worker(player):
                    actions.append(ct.build_worker())
                else:
                    actions.append(ct.research())

            if fulled:
                # choose a place to create a new citytile in same city
                for x, y in [(pxy.x, pxy.y+1), (pxy.x, pxy.y-1), (pxy.x+1, pxy.y), (pxy.x-1, pxy.y)]:
                    cell = game_state.map.get_cell(x, y)
                    # actions.append(annotate.text(x, y, f"{x},{y}"))

                    if cell.citytile:
                        continue
                    if cell.has_resource():
                        continue  
                    else:
                        # actions.append(annotate.x(x, y))
                        jobs.add(Task.BUILD, Position(x,y))
                        break
            else: # Ask for energy
                jobs.add(Task.ENERGIZE, ct.pos)

    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            my_job = jobs.jobRequest(unit)

            if my_job.task == Task.HARVEST:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    action = unit.move(unit.pos.direction_to(
                        my_job.pos))
                    actions.append(action)

            elif my_job.task == Task.ENERGIZE:
                if unit.pos == my_job.pos:
                    jobs.jobDone(unit.id)
                else:
                    action = unit.move(unit.pos.direction_to(
                        my_job.pos))
                    actions.append(action)

            elif my_job.task == Task.BUILD:
                if unit.pos == my_job.pos:
                    action = unit.build_city()
                    actions.append(action)
                    jobs.jobDone(unit.id)
                else:
                    move_dir, path = game_state.path_to(unit.pos, my_job.pos, noCities=True)
                    actions.append(unit.move(move_dir))
                    # Draw the path
                    for i in range(len(path)-1):
                        actions.append(annotate.line(
                            path[i][1], path[i][2], path[i+1][1], path[i+1][2]))

    return actions




            # # we want to mine only if there is space left in the worker's cargo
            # if unit.get_cargo_space_left() > 0:
            #     # find the closest resource if it exists to this unit
            #     closest_resource_tile = find_closest_resources(
            #         unit.pos, player, game_state.resource_tiles)
            #     if closest_resource_tile is not None:
            #         # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
            #         # move_dir, path = game_state.path_to(unit.pos, closest_resource_tile.pos)
            #         # actions.append(unit.move(move_dir))
            #         # Draw the path
            #         # for i in range(len(path)-1):
            #         #    actions.append(annotate.line(path[i][1], path[i][2], path[i+1][1], path[i+1][2]))
            #         action = unit.move(unit.pos.direction_to(
            #             closest_resource_tile.pos))
            #         actions.append(action)
            # elif lets_build_city:
            #     # Annotate where to build
            #     actions.append(annotate.x(build_pos.x, build_pos.y))
            #     # if in build position -> create a citytile
            #     if unit.pos == build_pos:
            #         actions.append(unit.build_city())
            #         max_tiles += 1
            #         lets_build_city = False
            #     else:
            #         # move to the build_position
            #         move_dir, path = game_state.path_to(
            #             unit.pos, build_pos, noCities=True)
            #         actions.append(unit.move(move_dir))
            #         # Draw the path
            #         for i in range(len(path)-1):
            #             actions.append(annotate.line(
            #                 path[i][1], path[i][2], path[i+1][1], path[i+1][2]))

            # else:
            #     # find the closest citytile and move the unit towards it to drop resources to a citytile to fuel the city
            #     closest_city_tile = find_closest_city_tile(unit.pos, player)
            #     if closest_city_tile is not None:
            #         # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
            #         action = unit.move(
            #             unit.pos.direction_to(closest_city_tile.pos))
            #         actions.append(action)

