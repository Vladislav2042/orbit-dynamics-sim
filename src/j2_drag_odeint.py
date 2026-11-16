import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Константы
MU = 3.986004418e14  # м^3/с^2
R_E = 6.371e6  # м
J2 = 1.08262668e-3
Cd = 2.2  # коэффициент сопротивления
A_m = 0.1  # A/m, площадь/масса, м^2/кг (пример)
rho0 = 1e-12  # кг/м^3, базовая плотность на LEO
H = 100e3  # шкала высоты атмосферы, м


# Функция для плотности атмосферы (экспоненциальная модель)
def atmospheric_density(h):
    return rho0 * np.exp(-(h - 200e3) / H)  # пример для h > 200 км


# Уравнения движения в 2D (XY плоскость, экваториальная орбита)
def satellite_motion_2d(state, t):
    x, y, vx, vy = state
    r = np.array([x, y])
    r_norm = np.linalg.norm(r)
    h = r_norm - R_E  # высота

    # Гравитация
    a_grav = -MU * r / r_norm ** 3

    # J2 возмущение (упрощенное для 2D, предполагаем влияние на плоскости)
    # В 2D J2 моделируется как дополнительная сила от облиатности
    a_j2 = np.zeros(2)
    if r_norm > 0:
        a_j2 = - (3 / 2) * J2 * MU * (R_E / r_norm) ** 2 / r_norm ** 3 * np.array([
            x * (1 - 5 * (y / r_norm) ** 2),  # адаптировано, предполагая z=0, но для экватора J2 минимально
            y * (3 - 5 * (y / r_norm) ** 2)
        ])  # Упрощение; в реальности для экватора J2 влияет на радиус

    # Атмосферное сопротивление
    v = np.array([vx, vy])
    v_norm = np.linalg.norm(v)
    rho = atmospheric_density(h) if h > 0 else 0
    a_drag = -0.5 * Cd * rho * A_m * v_norm * v if v_norm > 0 else np.zeros(2)

    # Другие силы (солнечное давление, пример упрощенный)
    P_sun = 4.56e-6  # Па, солнечное давление
    a_srp = -P_sun * A_m * np.array([1, 0])  # предполагаем направление от Солнца沿 x

    # Суммарное ускорение
    a_total = a_grav + a_j2 + a_drag + a_srp

    return [vx, vy, a_total[0], a_total[1]]


# Начальные условия (круговая орбита, h=500 км)
h = 500e3
a = R_E + h
v0 = np.sqrt(MU / a)
state0 = [a, 0, 0, v0]  # x, y, vx, vy

# Время (1 сутки)
t = np.linspace(0, 86400, 10000)

# Интеграция
trajectory = odeint(satellite_motion_2d, state0, t)

# Визуализация
plt.plot(trajectory[:, 0], trajectory[:, 1])
plt.xlabel('X (m)')
plt.ylabel('Y (m)')
plt.title('2D Траектория спутника на LEO с силами')
plt.axis('equal')
plt.show()