import pandas as pd
import numpy as np
import numpy.ma as ma
import time
from datetime import datetime
from scipy.spatial.distance import cityblock


class Counter:
    def __init__(self, low, high):
        self.current = low
        self.high = high

    def __iter__(self):
        return self

    def __next__(self):
        if self.current > self.high:
            raise StopIteration
        else:
            self.current += 1
            return self.current - 1


class Vehicule:
    """
    Vehicules disponibles
    """
    def __init__(self):
        self._x = 0
        self._y = 0
        self.last_ride_duration = 0
        self.latest_finish = 0
        self.rides_affected = []

    def move(self, a, b):
        self._x = self._x + a
        self._y = self._y + b

    def ride_duration(self, a, b):
        T = (a - self._x) + (b - self._y)

    def availability(self):
        if T > 1:
            self.last_ride_duration = 0
        # TODO: step control

    def display(self):
        print('- Locate at ({}, {}) free at step : {}'.format(self._x, self._y, self.latest_finish))


class Grid(Vehicule, Counter):
    """
    Grid
    """
    def __init__(self):
        print("\n------ Initialise ------")
        self.load_input()
        self.R, self.C, self.F, self.N, self.B, self.T = map(int, self.dataraw.iloc[0].tolist())
        self.rides = self.dataraw[1:]
        # self._ride = Counter(1, self.N)
        self.fleet = dict.fromkeys(list(range(self.F)), Vehicule())
        # self.step = Counter(1, self.T)
        self.step = 1
        self.mtx = np.zeros((self.N, self.F))
        self.mask = np.zeros((self.N,self.F))
        self._ride_tmp = 0

    def load_input(self):
        """
        R – number of rows of the grid (1 ≤ R ≤ 10000)
        C – number of columns of the grid (1 ≤ C ≤ 10000)
        F – number of vehicles in the fleet (1 ≤ F ≤ 1000)
        N – number of rides (1 ≤ N ≤ 10000)
        B – per-ride bonus for starting the ride on time (1 ≤ B ≤ 10000)
        T – number of steps in the simulation (1 ≤ T ≤ 109)

        a_example.in
        b_should_be_easy.in
        """
        self.dataraw = pd.read_csv("b_should_be_easy.in", sep=" ", header=None)

    def print_param(self):
        print('\n------ Parameters ------')
        print("\n R (rows) : {}\n C (columns) : {}\n F (number of cars in fleet) : {}\n N (Number of rides) : {}\n B (bonus) : {}\n T (steps) : {}"\
            .format(self.R, self.C, self.F, self.N, self.B, self.T))

        self.rides.columns = ['a', 'b', 'x', 'y', 's', 'f']
        self.rides = self.rides.reset_index(drop=True)
        self.rides = self.rides.to_dict('index')
        # print("\n------ Rides ------")
        # print(self.rides)

    def print_car(self):
        print("\n------ [step {}] Fleet ------".format(self.step))
        # for car in self.fleet:
        for car in range(0, 50, 10):
            print(' [{}] '.format(car), end='', flush=True)
            self.fleet[car].display()

    def lastest_finish(self, ride):
        if ride['f'] >= ride['s'] + abs(ride['x'] - ride['a']) + abs(ride['y'] - ride['b']):
            print('ok')
        if ride['f'] >= self.T:
            print('end')

    def compute(self):
        start = time()
        print("\n------ [step {}] Computing ------".format(self.step))
        affectations = []
        mtxm = ma.masked_array(self.mtx, mask=self.mask)

        for _ride in range(self._ride_tmp, self.N):

            mtxm = ma.masked_array(self.mtx, mask=self.mask)
            veh = np.argmax(mtxm[_ride])

            self.fleet[veh].rides_affected.append(_ride)
            self.fleet[veh].last_ride_duration = self.rides[_ride]['f'] - self.rides[_ride]['s']
            self.fleet[veh].latest_finish = self.rides[_ride]['f']
            self.fleet[veh].move(self.rides[_ride]['x'], self.rides[_ride]['y'])
            self.mask[:, veh] = 1

            # print('{} : {}'.format(_ride, veh))

            if len(affectations) == self.F:
                self.mask[_ride + 1:,:] = 0
                self._ride_tmp = _ride + 1
                print('All cars affected !!')
                break 

            for car in self.fleet:
                if self.fleet[car].latest_finish >= self.step:
                    self.mask[:, car] = 0
        
        mtxm = ma.masked_array(self.mtx, mask=self.mask)
        print(mtxm.shape)
        print(time() - start)

    def compute_earn(self, ride, car):
        distance = ride['f'] - ride['s']
        bonus = self.B
        return distance + bonus

    def compute_priority(self):
        for car in self.fleet:
            for ride in self.rides:
                self.mtx[ride][car] = max(self.rides[ride]['s'] - self.step - cityblock((self.rides[ride]['a'], self.rides[ride]['b']), (self.fleet[car]._x, self.fleet[car]._y)), 0)
        # print()
        # print(self.mtx)

    def select_ride(self):
        pass

    def submission(self):
        print('\n------ Writing output ------')
        output = open('submission_{}.csv'.format(datetime.now().strftime('%Y%m%d_%H%M%S')), 'w')
        for veh in self.fleet:
            output.writelines(' '.join(self.fleet[veh].rides_affected()))
        output.close()

"""
{1: {'a': 0, 'b': 0, 'f': 9, 's': 2, 'x': 1, 'y': 3},
 2: {'a': 1, 'b': 2, 'f': 9, 's': 0, 'x': 1, 'y': 0},
 3: {'a': 2, 'b': 0, 'f': 9, 's': 0, 'x': 2, 'y': 2}}
"""

if __name__ == "__main__":
    # execute simulation
    grid = Grid()
    grid.print_param()
    grid.print_car()

    # grid.compute_priority()
    # grid.compute()
    # grid.print_car()

    for stp in range(1, 25000):
        grid.step = stp
        grid.compute_priority()
        grid.compute()
        grid.print_car()

    grid.submission()


