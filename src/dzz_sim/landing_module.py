
import numpy as np
import config as cfg
from landing_leg import LandingLeg

class LandingModule:
    def __init__(self):
        self.state = np.concatenate((cfg.INITIAL_POSITION, cfg.INITIAL_VELOCITY))  # [x, y, vx, vy]
        self.thrust = 0.0
        self.leg = LandingLeg()
        self.history = {'t': [], 'y': [], 'vy': []}
        self.time = 0.0
        self.landed = False

    def dynamics(self, state):
        y, vy = state[1], state[3]
        accel_grav = -cfg.G
        accel_thrust = self.thrust / cfg.MODULE_MASS
        leg_force = self.leg.update(y, vy)
        accel_leg = leg_force / cfg.MODULE_MASS if leg_force > 0 else 0
        return accel_grav + accel_thrust + accel_leg

    def update(self, dt):
        vy = self.state[3]
        accel = self.dynamics(self.state)
        self.state[3] += accel * dt
        self.state[1] += vy * dt + 0.5 * accel * dt**2
        self.time += dt

        if self.state[1] <= 0:
            self.landed = True

        self.history['t'].append(self.time)
        self.history['y'].append(self.state[1])
        self.history['vy'].append(self.state[3])