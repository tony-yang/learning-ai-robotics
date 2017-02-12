# -----------
# User Instructions
#
# Implement a PD controller by running 100 iterations
# of robot motion. The steering angle should be set
# by the parameter tau so that:
#
# steering = -tau_p * CTE - tau_d * diff_CTE
# where differential crosstrack error (diff_CTE)
# is given by CTE(t) - CTE(t-1)
#
# Your code should print output that looks like
# the output shown in the video.
#
# Only modify code at the bottom!
# ------------

from math import *
import random

class robot:
    def __init__(self, length = 20.0):
        self.x = 0.0
        self.y = 0.0
        self.orientation = 0.0
        self.length = length
        self.steering_noise = 0.0
        self.distance_noise = 0.0
        self.steering_drift = 0.0

    def set(self, new_x, new_y, new_orientation):
        self.x = float(new_x)
        self.y = float(new_y)
        self.orientation = float(new_orientation) % (2.0 * pi)

    def set_noise(self, new_s_noise, new_d_noise):
        # makes it possible to change the noise parameters
        # this is often useful in particle filters
        self.steering_noise = float(new_s_noise)
        self.distance_noise = float(new_d_noise)

    def set_steering_drift(self, drift):
        self.steering_drift = drift

    # --------
    # move:
    #    steering = front wheel steering angle, limited by max_steering_angle
    #    distance = total distance driven, most be non-negative

    def move(self, steering, distance, tolerance = 0.001, max_steering_angle = pi / 4.0):
        if steering > max_steering_angle:
            steering = max_steering_angle
        if steering < -max_steering_angle:
            steering = -max_steering_angle
        if distance < 0.0:
            distance = 0.0

        # make a new copy
        res = robot()
        res.length         = self.length
        res.steering_noise = self.steering_noise
        res.distance_noise = self.distance_noise
        res.steering_drift = self.steering_drift

        # apply noise
        steering2 = random.gauss(steering, self.steering_noise)
        distance2 = random.gauss(distance, self.distance_noise)

        # apply steering drift
        steering2 += self.steering_drift

        # Execute motion
        turn = tan(steering2) * distance2 / res.length

        if abs(turn) < tolerance:
            # approximate by straight line motion
            res.x = self.x + (distance2 * cos(self.orientation))
            res.y = self.y + (distance2 * sin(self.orientation))
            res.orientation = (self.orientation + turn) % (2.0 * pi)
        else:
            # approximate bicycle model for motion
            radius = distance2 / turn
            cx = self.x - (sin(self.orientation) * radius)
            cy = self.y + (cos(self.orientation) * radius)
            res.orientation = (self.orientation + turn) % (2.0 * pi)
            res.x = cx + (sin(res.orientation) * radius)
            res.y = cy - (cos(res.orientation) * radius)
        return res

    def __repr__(self):
        return '[x={:.5f} y={:.5f} orient={:.5f}]'.format(self.x, self.y, self.orientation)


def run(params, printflag = False):
    myrobot = robot()
    myrobot.set(0.0, 1.0, 0.0)
    speed = 1.0 # motion distance is equal to speed (we assume time = 1)
    err = 0.0

    N = 100
    myrobot.set_steering_drift(10.0 / 180.0 * pi)

    crosstrack_error = myrobot.y
    previous_crosstrack_error = myrobot.y
    crosstrack_error_sum = 0.0
    for i in range(N * 2):
        crosstrack_error = myrobot.y
        crosstrack_error_sum += crosstrack_error
        new_steering_angle = (-params[0] * crosstrack_error
            - params[1] * (crosstrack_error - previous_crosstrack_error)
            - params[2] * crosstrack_error_sum)

        myrobot = myrobot.move(new_steering_angle, speed)
        previous_crosstrack_error = crosstrack_error

        if i >= N:
            err += (crosstrack_error ** 2)
        if printflag:
            print(myrobot, new_steering_angle / pi * 180.0)

    return err / float(N)

def twiddle(tolerance = 0.001):
    params = [0.0, 0.0, 0.0]
    params_difference = [1.0 for i in params]
    best_error = run(params)
    iteration = 1
    while sum(params_difference) > tolerance:
        for i in range(len(params)):
            params[i] += params_difference[i]
            error = run(params)
#            print('   == intermediate error = ', error)
            if error < best_error:
                best_error = error
                params_difference[i] *= 1.1
#                print('      error < best error parms_diff = ', params_difference)
            else:
                params[i] -= 2 * params_difference[i]
                error = run(params)
#                print('      error > best error parms = ', params, ' and error = ', error)
                if error < best_error:
                    best_error = error
                    params_difference[i] *= 1.1
                else:
                    params[i] += params_difference[i]
#                    print('      error > best error parms = ', params, ' params return ', params)
                    params_difference[i] *= 0.9
        print('Twiddle # {} {} -> {}'.format(iteration, params, best_error))
        iteration += 1

    return params

params = twiddle()
err = run(params, True)
print('\nFinal parameters: ', params, '\n -> ', err)
