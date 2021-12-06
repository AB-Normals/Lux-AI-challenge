# used to test for correctness of functions

from abn.game_ext import GameExtended
from abn.jobs import JobBoard, Job, Task
from lux.game_objects import Unit, City, Player
from lux.game_map import Position
from lux.constants import Constants

UNIT_TYPES = Constants.UNIT_TYPES

###############################################################################
# USEFUL FUNCTIONS
###############################################################################
def print_jobs(jobs):
    inprog = [v for v in jobs.inprogress.values()]
    l = max(len(inprog), len(jobs.todo))
    #js = zip(jobs.todo + [""] * l, inprog + [""] * l)[:l]
    js = list(zip(jobs.todo + [""] * l, inprog + [""] * l))[:l]
    print ('{:28s} | {:28s}'.format("TODO", "INPROGRESS"))
    print ('{:28s}-+-{:28s}'.format("-" * 28, "-" * 28))
    for j in js:
        s1 = str(j[0])
        s2 = str(j[1])
        print ('{:28} | {:28}'.format(s1, s2))
    print ('{:28s}-+-{:28s}'.format("-" * 28, "-" * 28))
###############################################################################

game_state = GameExtended()
jobs = game_state.job_board

# create a player
player = Player(0)

# create cities
city1 = City(0, "c_1", 0, 0)
city2 = City(0, "c_2", 0, 0)
# add citytiles to cities
city1._add_city_tile(10, 10, 0)
city1._add_city_tile(10, 11, 0)
city2._add_city_tile(20, 10, 0)
city2._add_city_tile(20, 11, 0)
player.cities[city1.cityid] = city1
player.cities[city2.cityid] = city2

# create Units
unit1 = Unit(0, UNIT_TYPES.WORKER, "u_1", 10, 10, 0, 0 ,0, 0)
unit2 = Unit(0, UNIT_TYPES.WORKER, "u_2", 20, 10, 0, 0 ,0, 0)
unit3 = Unit(0, UNIT_TYPES.WORKER, "u_3", 25, 10, 0, 0 ,0, 0)
player.units.append(unit1)
player.units.append(unit2)
player.units.append(unit3)

print ("---------------")
print (f"Player Units  : {[u.id for u in player.units]}")
print (f"Player Cities : {[c for c in player.cities]}")
print ("---------------")

# Add some jobs to the JobBoard
jobs.addJob(Task.ENERGIZE, Position(10,10), city_id=city1.cityid)
jobs.addJob(Task.BUILD, Position(15,10), city_id=city1.cityid)
jobs.addJob(Task.EXPLORE, Position(1,1), city_id=city1.cityid)
jobs.addJob(Task.EXPLORE, Position(-1,-1))
jobs.addJob(Task.ENERGIZE, Position(20,10), city_id=city2.cityid)
jobs.addJob(Task.BUILD, Position(25,10), city_id=city2.cityid)
jobs.addJob(Task.EXPLORE, Position(12,12), city_id=city2.cityid)

print ()
print ("All JOBS inserted")
print()
print_jobs(jobs)

# Each unit ask for a job
j1 = jobs.jobRequest(unit1)
j2 = jobs.jobRequest(unit2)
j3 = jobs.jobRequest(unit3)

jobs.checkActiveJobs(player.units, player.cities)

print ()
print ("After 3 jobs requests")
print()
print_jobs(jobs)

del player.cities[city1.cityid]
del player.units[2]

jobs.checkActiveJobs(player.units, player.cities)

print ()
print ("After removing c_1 e u_3")
print()
print_jobs(jobs)
