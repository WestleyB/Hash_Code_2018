import pandas as pd
import numpy as np
import numpy.ma as ma
import time
from datetime import datetime
from scipy.spatial.distance import cityblock
import logging


class Stepper:
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

    def update(self, goto):
        self.current = goto


class Rider:
    """
    Riders
    """
    def __init__(self):
        self._x = 0
        self._y = 0
        self.end_of_current_ride = 0
        self.rides_affected = []

    def move(self, a, b):
        self._x = a
        self._y = b

    def ride_duration(self, a, b):
        T = abs(a - self._x) + abs(b - self._y)

    def set_availability(self, step_end):
        self.end_of_current_ride = step_end

    def get_availability(self):
        return self.end_of_current_ride

    def affect_ride(self, ride):
        self.rides_affected.append(ride)

    def display(self):
        print('- Locate at ({}, {}) free at step : {}'.format(self._x, self._y, self.end_of_current_ride), flush=False)

    def get_rides(self):
        return self.rides_affected


class Grid(Rider, Stepper):
    """
    Map
    """
    def __init__(self):
        """
        a_example.in
        b_should_be_easy.in
        c_no_hurry.in
        """
        print("\n------ Initialise ------")
        self.filename = "data/b_should_be_easy.in"
        self.load_input()
        self.R, self.C, self.F, self.N, self.B, self.T = map(int, self.dataraw.iloc[0].tolist())
        self.rides = self.dataraw[1:]
        # self.fleet = dict.fromkeys(list(range(self.F)), Rider())
        self.fleet = { key : Rider() for key in list(range(self.F)) }
        self.stepper = Stepper(0, self.T - 1)
        self.step = 0
        self.mtx = np.zeros((self.N, self.F))
        self.mask_riders = np.zeros((self.N,self.F))
        self.mask_rides = np.zeros((self.N,self.F))
        self.mask_lates = np.zeros((self.N,self.F))
        self._ride_tmp = 0
        self.riders_affected = []

    def load_input(self):
        """
        R – number of rows of the grid (1 ≤ R ≤ 10000)
        C – number of columns of the grid (1 ≤ C ≤ 10000)
        F – number of vehicles in the fleet (1 ≤ F ≤ 1000)
        N – number of rides (1 ≤ N ≤ 10000)
        B – per-ride bonus for starting the ride on time (1 ≤ B ≤ 10000)
        T – number of steps in the simulation (1 ≤ T ≤ 109)
        """
        self.dataraw = pd.read_csv(self.filename, sep=" ", header=None)

    def next(self):
        self.step = self.stepper.__next__()

    def print_param(self):
        print('\n------ Parameters ------')
        print("\n R (rows) : {}\n C (columns) : {}\n F (number of cars in fleet) : {}\n N (Number of rides) : {}\n B (bonus) : {}\n T (steps) : {}"\
            .format(self.R, self.C, self.F, self.N, self.B, self.T))

        self.rides.columns = ['a', 'b', 'x', 'y', 's', 'f']
        self.rides = self.rides.reset_index(drop=True)
        self.rides = self.rides.to_dict('index')
        
        # print("\n------ Rides ------\n")
        # print(self.rides)

    def print_car(self):
        print("\n------ [step {}] Fleet ------".format(self.step))
        for car in self.fleet:
            print(' [{}] '.format(car), end='', flush=True)
            self.fleet[car].display()

    def lastest_finish(self, ride):
        if ride['f'] >= ride['s'] + abs(ride['x'] - ride['a']) + abs(ride['y'] - ride['b']):
            print('ok')
        if ride['f'] >= self.T:
            print('end')

    def compute(self):
        print("\n------ [step {}] Computing ------".format(self.step))

        for _ride in range(self._ride_tmp, self.N):

            # print(" [x] Compute ride #{} ............ ".format(_ride), end='', flush=True)
            mtxm_1 = ma.masked_array(self.mtx, mask=self.mask_riders)
            mtxm_2 = ma.masked_array(mtxm_1, mask=self.mask_rides)
            mtxm_3 = ma.masked_where(mtxm_2 < 0, mtxm_2)

            if type(np.min(mtxm_3[_ride])) != ma.core.MaskedConstant:
                veh = np.argmin(mtxm_3[_ride])
                self.riders_affected.append(veh)
                self.fleet[veh].affect_ride(_ride)
                self.fleet[veh].set_availability(self.step + cityblock((self.rides[_ride]['a'], self.rides[_ride]['b']), (self.fleet[veh]._x, self.fleet[veh]._y)))
                self.fleet[veh].move(self.rides[_ride]['x'], self.rides[_ride]['y'])
                self.mask_riders[:, veh] = 1
                self.mask_rides[_ride, :] = 1
                # print('affected to rider #{} ({}:{})'.format(veh, self.fleet[veh]._x, self.fleet[veh]._y), flush=False)
            else:
                # print('no riders available', flush=False)
                pass

            if _ride >= self.N:
                print('\nAll rides done !!!\n')
                break

    def check_availability(self):
        print("\n------ [step {}] Checking availability ------".format(self.step))
        step_tmp = 999999999999
        for car in self.fleet:
            preview_step = self.fleet[car].get_availability()
            if preview_step <= self.step:
                self.mask_riders[:, car] = 0
                # print(' [{}] arrived to ({}:{}) at step {}'.format(car, self.fleet[car]._x, self.fleet[car]._y, preview_step))

        # Avance rapide (0.6s -> 0.8s )
            if preview_step > self.step and preview_step < step_tmp and preview_step != 0:
                # print(preview_step)
                step_tmp = preview_step
        # print('>>>>> Go To step {}'.format(step_tmp))
        self.stepper.update(step_tmp if step_tmp < 999999999999 else self.step + 1)

    def compute_earn(self, ride, car):
        distance = ride['f'] - ride['s']
        bonus = self.B
        return distance + bonus

    def compute_priority(self):
        for car in self.fleet:
            for ride in self.rides:
                self.mtx[ride][car] =  abs(self.rides[ride]['a'] - self.fleet[car]._x) + abs(self.rides[ride]['b'] - self.fleet[car]._y) - (self.rides[ride]['s'] - self.step)

    def submission(self):
        print('\n------ Writing output ------')
        total_rides = 0
        output = open('submissions/{}_submission_{}.csv'.format(self.filename[:1], datetime.now().strftime('%Y%m%d_%H%M%S')), 'w')
        for veh in self.fleet:
            _rides = self.fleet[veh].get_rides()
            total_rides += len(_rides)
            print(_rides)
            output.write(str(len(_rides)) + ' ' + ' '.join(str(r) for r in _rides) + '\n')
        output.close()
        print('\nTotal rides {}'.format(total_rides))


if __name__ == "__main__":
    start = time.time()

    # execute simulation
    grid = Grid()
    grid.print_param()
    grid.print_car()

    while True:
         try:
            grid.check_availability()
            grid.next()
            grid.compute_priority()
            grid.compute()
            # grid.print_car()
            if grid.step >= grid.T:
                break
         except StopIteration:
             break

    grid.submission()
    print('\nExecution finished in {:.2f}s'.format(time.time() - start))


