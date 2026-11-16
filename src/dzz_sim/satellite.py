import numpy as np
import config as cfg


class Satellite:
    """Математическая модель спутника ДЗЗ на НОО"""

    def __init__(self, mass=None, cross_section=None):
        self.mass = mass if mass else cfg.MASS
        self.cross_section = cross_section if cross_section else cfg.CROSS_SECTION

        # Начальное состояние: [x, y, z, vx, vy, vz]
        self.state = np.concatenate((cfg.INITIAL_POSITION, cfg.INITIAL_VELOCITY))
        self.time = 0.0

        # История для анализа
        self.history = {
            't': [], 'x': [], 'y': [], 'z': [],
            'vx': [], 'vy': [], 'vz': [],
            'altitude': [], 'velocity': [], 'eccentricity': []
        }

        # Орбитальные элементы
        self.update_orbital_elements()

    def update_orbital_elements(self):
        """Вычисление орбитальных элементов"""
        pos = self.state[:3]
        vel = self.state[3:]
        r = np.linalg.norm(pos)
        v = np.linalg.norm(vel)

        # Удельный момент количества движения
        h = np.cross(pos, vel)
        h_mag = np.linalg.norm(h)

        # Вектор эксцентриситета
        if h_mag > 0:
            e_vec = np.cross(vel, h) / cfg.G / cfg.M_EARTH - pos / r
            eccentricity = np.linalg.norm(e_vec)
        else:
            eccentricity = 0.0

        # Удельная орбитальная энергия
        energy = v ** 2 / 2 - cfg.G * cfg.M_EARTH / r

        # Большая полуось
        semi_major = -cfg.G * cfg.M_EARTH / (2 * energy) if abs(energy) > 1e-10 else float('inf')

        # Сохранение элементов
        self.orbital_elements = {
            'semi_major_axis': semi_major,
            'eccentricity': eccentricity,
            'energy': energy,
            'angular_momentum': h_mag,
            'radius': r,
            'velocity': v,
            'period': 2 * np.pi * np.sqrt(semi_major ** 3 / cfg.G / cfg.M_EARTH) if semi_major != float('inf') else 0
        }

    def atmospheric_density(self, altitude):
        """Экспоненциальная модель атмосферы"""
        if altitude < 0:
            return cfg.RHO0
        elif altitude < 100e3:  # До 100 км
            return cfg.RHO0 * np.exp(-altitude / cfg.H_SCALE)
        else:  # Выше 100 км (очень разреженная)
            return 1e-10 * np.exp(-(altitude - 100e3) / 50e3)

    def gravitational_acceleration(self, pos):
        """Ускорение от гравитации с учетом J2"""
        r = np.linalg.norm(pos)
        x, y, z = pos

        # Центральное гравитационное ускорение
        a_central = -cfg.G * cfg.M_EARTH / r ** 3 * pos

        # Поправка J2 (несферичность Земли)
        if cfg.J2 > 0:
            factor = 3 / 2 * cfg.J2 * (cfg.R_EARTH / r) ** 2
            a_j2 = np.array([
                x / r * (5 * z ** 2 / r ** 2 - 1),
                y / r * (5 * z ** 2 / r ** 2 - 1),
                z / r * (5 * z ** 2 / r ** 2 - 3)
            ])
            a_j2 *= factor * cfg.G * cfg.M_EARTH / r ** 2
            a_central += a_j2

        return a_central

    def drag_acceleration(self, pos, vel):
        """Ускорение от атмосферного сопротивления"""
        altitude = np.linalg.norm(pos) - cfg.R_EARTH

        if altitude < 1000e3:  # Эффект существенен до 1000 км
            rho = self.atmospheric_density(altitude)

            # Учет вращения атмосферы
            v_atm = np.cross([0, 0, cfg.OMEGA_EARTH], pos)
            v_rel = vel - v_atm
            v_mag = np.linalg.norm(v_rel)

            if v_mag > 0:
                # F_drag = 0.5 * ρ * Cd * A * v²
                drag_mag = 0.5 * rho * cfg.DRAG_COEFF * self.cross_section * v_mag ** 2 / self.mass
                return -drag_mag * v_rel / v_mag

        return np.zeros(3)

    def total_acceleration(self):
        """Суммарное ускорение"""
        pos = self.state[:3]
        vel = self.state[3:]
        return self.gravitational_acceleration(pos) + self.drag_acceleration(pos, vel)

    def rk4_step(self, dt):
        """Метод Рунге-Кутты 4-го порядка"""

        def f(state):
            vel = state[3:]
            acc = self.total_acceleration()
            return np.concatenate((vel, acc))

        k1 = f(self.state)
        k2 = f(self.state + 0.5 * dt * k1)
        k3 = f(self.state + 0.5 * dt * k2)
        k4 = f(self.state + dt * k3)

        self.state += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        self.time += dt

    def save_state(self):
        """Сохранение текущего состояния"""
        pos = self.state[:3]
        vel = self.state[3:]
        altitude = np.linalg.norm(pos) - cfg.R_EARTH

        self.history['t'].append(self.time)
        self.history['x'].append(pos[0])
        self.history['y'].append(pos[1])
        self.history['z'].append(pos[2])
        self.history['vx'].append(vel[0])
        self.history['vy'].append(vel[1])
        self.history['vz'].append(vel[2])
        self.history['altitude'].append(altitude)
        self.history['velocity'].append(np.linalg.norm(vel))

        self.update_orbital_elements()
        self.history['eccentricity'].append(self.orbital_elements['eccentricity'])

    def update(self, dt=None):
        """Обновление состояния спутника"""
        if dt is None:
            dt = cfg.TIME_STEP

        # Интегрирование уравнений движения
        self.rk4_step(dt)

        # Сохранение состояния
        if self.time % cfg.OUTPUT_INTERVAL < dt:
            self.save_state()

        # Проверка на столкновение с Землей
        altitude = np.linalg.norm(self.state[:3]) - cfg.R_EARTH
        if altitude < 0:
            return False

        return True