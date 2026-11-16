import matplotlib.pyplot as plt
import numpy as np
import config as cfg


def plot_results(satellite):
    """Построение графиков результатов моделирования"""
    if len(satellite.history['t']) < 10:
        print("Недостаточно данных для построения графиков")
        return

    t = np.array(satellite.history['t']) / 3600  # часы
    altitude = np.array(satellite.history['altitude']) / 1000  # км
    velocity = np.array(satellite.history['velocity']) / 1000  # км/с
    eccentricity = np.array(satellite.history['eccentricity'])

    # Создание графиков
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Результаты моделирования ДЗЗ-спутника на НОО', fontsize=16, fontweight='bold')

    # 1. Высота орбиты
    ax1 = axes[0, 0]
    ax1.plot(t, altitude, 'b-', linewidth=2)
    ax1.axhline(y=cfg.LEO_HEIGHT / 1000, color='r', linestyle='--', alpha=0.5, label='НОО (400 км)')
    ax1.set_xlabel('Время, ч')
    ax1.set_ylabel('Высота, км')
    ax1.set_title('Изменение высоты орбиты')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 2. Скорость
    ax2 = axes[0, 1]
    ax2.plot(t, velocity, 'g-', linewidth=2)
    ax2.axhline(y=cfg.ORBITAL_VELOCITY / 1000, color='r', linestyle='--', alpha=0.5,
                label=f'Круговая ({cfg.ORBITAL_VELOCITY / 1000:.3f} км/с)')
    ax2.set_xlabel('Время, ч')
    ax2.set_ylabel('Скорость, км/с')
    ax2.set_title('Орбитальная скорость')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # 3. Эксцентриситет
    ax3 = axes[1, 0]
    ax3.plot(t, eccentricity, 'm-', linewidth=2)
    ax3.set_xlabel('Время, ч')
    ax3.set_ylabel('Эксцентриситет')
    ax3.set_title('Эволюция эксцентриситета')
    ax3.grid(True, alpha=0.3)
    ax3.set_yscale('log')

    # 4. Траектория в плоскости XY
    ax4 = axes[1, 1]
    x = np.array(satellite.history['x']) / 1000
    y = np.array(satellite.history['y']) / 1000

    # Земля
    earth = plt.Circle((0, 0), cfg.R_EARTH / 1000, color='blue', alpha=0.5, label='Земля')
    ax4.add_patch(earth)

    # Орбита
    ax4.plot(x, y, 'r-', linewidth=1, alpha=0.7, label='Траектория')
    ax4.plot(x[0], y[0], 'go', markersize=8, label='Старт')
    if len(x) > 100:
        ax4.plot(x[-1], y[-1], 'ro', markersize=8, label='Конец')

    ax4.set_xlabel('X, км')
    ax4.set_ylabel('Y, км')
    ax4.set_title('Орбита в плоскости XY')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.axis('equal')

    plt.tight_layout()
    plt.show()

    # Дополнительный 3D график
    if len(x) > 100:
        fig_3d = plt.figure(figsize=(10, 8))
        ax_3d = fig_3d.add_subplot(111, projection='3d')
        z = np.array(satellite.history['z']) / 1000

        ax_3d.plot(x, y, z, 'b-', alpha=0.7, linewidth=1)
        ax_3d.scatter(x[0], y[0], z[0], color='green', s=50, label='Старт')
        ax_3d.scatter(x[-1], y[-1], z[-1], color='red', s=50, label='Конец')

        ax_3d.set_xlabel('X, км')
        ax_3d.set_ylabel('Y, км')
        ax_3d.set_zlabel('Z, км')
        ax_3d.set_title('3D траектория спутника')
        ax_3d.legend()
        ax_3d.grid(True, alpha=0.3)

        plt.show()