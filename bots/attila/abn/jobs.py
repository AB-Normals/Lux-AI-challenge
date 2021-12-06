# Job
# ---
# The "Employment Office" for the Units 

import math
from typing import Tuple, List, Dict
from lux.game_map import Position, Cell
from lux.game_objects import Unit
class Task:
    """
    Each task consist on a type of Job for a single unit.
    The Task has to be done on a specified position, so the task is always 
    movement and then the Job
    """
    SLEEP = "r"         # Sleep until daytime
    BUILD = "b"         # Build a citytile of city 'city_id' at 'pos' 
    HARVEST = "h"       # Get resouce at 'pos'
    ENERGIZE = "e"      # Feed a 'city_id' with resource ad return it at 'pos'
    EXPLORE = "x"       # Search for a place to build a new city
    INVASION = "i"      # Invade a city

def TaskStr(task: str) -> str:
    _strings_ = {
        Task.SLEEP: "SLP",
        Task.BUILD: "BLD",
        Task.HARVEST: "HRV",
        Task.ENERGIZE: "NRG",
        Task.EXPLORE: "XPL",
        Task.INVASION: "IVS"
    }

    return(_strings_[task])
class Job:
    def __init__(self, task: str, pos: Position):
        self.pos: Position = pos    # some task need a position reference
        self.task: str = task       # task type
        self.city_id: str = ""      # city_id parameter used by some tasks
        self.unit_id: str = ""      # unit_id that has this task as assignement
        self.subtask: int = 0       # subtask used by jobs with multistate tasks 
        self.isNew : bool = True    # True if this job is assigned to a new unit
        self.data   = {}              # Data storage for multistate tasks

    def __str__(self):
        return f"{self.unit_id}: {TaskStr(self.task)}.{self.subtask} {self.pos} c:{self.city_id}"

class JobBoard:
    """
    This is a Bulletin Board with 3 different lists:
    - todo : list of jobs no-one has in charge
    - inprogress : jobs currently in progress (with unit who has the assignement)
    - done : completed jobs (only for debug pouposes) 
    """

    def __init__(self, parent):
        self.todo: List[Job] = []        # ToDo Jobs
        self.inprogress: Dict = {}  # InProgress Jobs
        self.done: List = []        # Done Jobs
        self.rip: List = []         # Dead Units
        self.parent = parent

    def _nextJob(self, unit: Unit):
        # TODO: need a heuristics for job selection based on different parameters:
        #       as unit position, time of day, priority.
        #       Now no heurostics
        if self.todo:
            closest_dist = math.inf
            score = 0
            i = None
            for n in range(len(self.todo)):
                if self.todo[n].unit_id == unit.id: # not rejected job by this unit
                    continue
                if not self.todo[n].pos:
                    distance = 100 # fake distance for jobs without position
                else:
                    distance = unit.pos.distance_to(self.todo[n].pos)
                

                if self.todo[n].task == Task.ENERGIZE:  # if not reacheable result is 0
                    temp_score = 1      
                elif self.todo[n].task == Task.BUILD:     # if not reacheable result is 0
                    temp_score = 0.5
                elif self.todo[n].task == Task.INVASION:  # in this job unit starts by loading resources
                    temp_score = 0.2                     # so even if not reachable, it is not a problem
                elif self.todo[n].task == Task.EXPLORE:   # in this job unit starts by loading resources
                    temp_score = 0.2                     # so even if not reachable, it is not a problem
                else:
                    temp_score = 0.1

                if distance < closest_dist:
                    closest_dist = distance
                    score = temp_score
                    i = n
                elif distance == closest_dist:
                    if temp_score > score:
                        score = temp_score
                        i = n

                if temp_score > score:
                    i = n
                    score = temp_score            

            if i is not None:
                return self.todo.pop(i)
            else:
                return None
        else:
            # TODO: choose a default Job
            return None

    def _activeJobs(self):
        """ Return a list with all active Jobs (not DONE) """
        return self.todo + [n for n in self.inprogress.values()]

    def addJob(self, task: str, pos: Position, city_id: str = "") -> bool:
        # Check if no other active jobs are present for that position
        if not pos in [ j.pos for j in self._activeJobs()]:
            job = Job(task, pos)
            job.city_id = city_id
            self.todo.append(job)
            return True
        else:
            return False
    
    def jobReject(self, unit_id: str):
        """
        The rejected job is returned from inProgress to ToDo list, 
        mantains the unit_id so this job will not be assigned to the unit
        that rejected it.
        """
        if unit_id in self.inprogress:
            j = self.inprogress[unit_id]
            j.subtask = 0
            self.todo.append(j)
            del self.inprogress[unit_id]

    def count(self, task: str, pos: Position = None, city_id: str = "") -> int:
        """
        Return total number of active (not DONE) tasks with given parameters
        """
        retvalue = 0
        # check in self.todo 
        for job in self._activeJobs():
            if job.task == task:                
                if pos and pos != job.pos:
                    continue
                if city_id and city_id != job.city_id:
                    continue
                retvalue += 1
        return retvalue 

    def jobRequest(self, unit: Unit):
        """ 
        Unit can ask for a job, the function returns:
        - an 'inprogress' job for that unit_id if it's present
        - a new job from the 'todo' list
        """
        job = self.inprogress.get(unit.id)
        if job:
            # if is night then drop all Explore, Build and Invasion jobs
#            if self.parent.isNight() and job.task in [Task.EXPLORE, Task.INVASION]:
#                self.jobDrop(unit.id)
#            else:
                job.isNew = False
                return job
        # get a new job
        job = self._nextJob(unit)
        if job:            
            job.unit_id = unit.id
            job.isNew = True
            job.subtask = 0
            self.inprogress[unit.id] = job
            return job
#        elif self.parent.time < 15:
#            if self.parent.time % 2: 
#                job = Job(Task.EXPLORE, unit.pos)
#            else:
#                job = Job(Task.INVASION, unit.pos)
#            job.isNew = True
#            job.unit_id = unit.id
#            self.inprogress[unit.id] = job
#            return job
        else: # none to do -> EXPLORE
            job = Job(Task.EXPLORE, unit.pos)
#            job = Job(Task.HARVEST, unit.pos)
            job.isNew = True
            job.unit_id = unit.id
            self.inprogress[unit.id] = job
            return job
        
    def jobDone(self, unit_id):
        job = self.inprogress.get(unit_id)
        if job:
            self.done.append(job)
            del self.inprogress[unit_id]

    def jobDrop(self, unit_id):
        job = self.inprogress.get(unit_id)
        if job:
            del self.inprogress[unit_id]


    def activeJobToPos(self, pos: Position) -> bool:
        return pos in [j.pos for j in self.inprogress.values()]

    def checkActiveJobs(self, units : List, cities : List):
        """ 
        Remove Jobs assigned to dead units and created by a destroyed city
        1.  Using list of Units check if there are some InProgress Jobs assigned to 
            Unit no more on the list (dead unit). If the case:
            - return Job to ToDos
            - add dead unit.id to rip List
        2.  Using list of cities check in ToDo and InProgress Jobs created by a
            city no more on the list (destroyed city). In that case:
            - drop (remove) that job 
        """
        morgue = []
        for unit_id in self.inprogress:
            if unit_id not in [u.id for u in units]:
                morgue.append(unit_id)
        for unit_id in morgue:
            # mov job to self.todo
            self.jobDrop(unit_id)
            # add unit_id in self.rip
            self.rip.append(unit_id)
        # Create a new self.todo array removing jobs created by destroyed cities
        self.todo = [j for j in self.todo if (not j.city_id) or j.city_id in cities]
        # Create a new self.inprogress array removing jobs created by destroyed cities
        self.inprogress = {k:v for k,v in self.inprogress.items() if (not v.city_id) or v.city_id in cities}
        
