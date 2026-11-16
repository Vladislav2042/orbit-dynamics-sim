import numpy as np
import config as cfg
from satellite import Satellite
from simulator import Simulator
from plotter import plot_results


def main():
    """Основная функция запуска модели ДЗЗ-спутника"""
    print("=" * 70)
    print("МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ДЗЗ-СПУТНИКА НА НИЗКОЙ ОКОЛОЗЕМНОЙ ОРБИТЕ")
    print("=" * 70)

    print("\nПАРАМЕТРЫ МОДЕЛИ:")
    print(f"  • Высота орбиты: {cfg.LEO_HEIGHT / 1000:.0f} км")
    print(f"  • Начальная скорость: {cfg.ORBITAL_VELOCITY / 1000:.3f} км/с")
    print(f"  • Масса спутника: {cfg.MASS} кг")
    print(f"  • Площадь сечения: {cfg.CROSS_SECTION} м²")
    print(f"  • Длительность симуляции: {cfg.SIMULATION_DURATION / 3600:.1f} ч")
    print(f"  • Шаг интегрирования: {cfg.TIME_STEP} с")

    print("\nУЧИТЫВАЕМЫЕ ЭФФЕКТЫ:")
    print("  1. Гравитация Земли (точечная масса + гармоника J₂)")
    print("  2. Атмосферное сопротивление (экспоненциальная модель)")
    print("  3. Вращение атмосферы")

    print("\n" + "=" * 70)

    # Создание модели спутника
    print("Создание модели ДЗЗ-спутника...")
    satellite = Satellite()

    # Проверка начальных условий
    init_altitude = np.linalg.norm(satellite.state[:3]) - cfg.R_EARTH
    init_velocity = np.linalg.norm(satellite.state[3:])

    print(f"\nНАЧАЛЬНЫЕ УСЛОВИЯ:")
    print(f"  • Высота: {init_altitude / 1000:.1f} км")
    print(f"  • Скорость: {init_velocity / 1000:.3f} км/с")
    print(f"  • Орбитальный период: {2 * np.pi * np.sqrt(cfg.ORBIT_RADIUS ** 3 / cfg.G / cfg.M_EARTH) / 60:.1f} мин")

    print("\n" + "=" * 70)
    print("ЗАПУСК ВИЗУАЛИЗАЦИИ...")
    print("=" * 70)

    print("\nУПРАВЛЕНИЕ В СИМУЛЯТОРЕ:")
    print("  • ESC - выход")
    print("  • ПРОБЕЛ - пауза/продолжение")
    print("  • +/- - изменение масштаба")
    print("  • R - сброс масштаба")
    print("=" * 70)

    # Запуск симуляции
    try:
        simulator = Simulator(satellite)
        simulator.run()
    except Exception as e:
        print(f"Ошибка в симуляторе: {e}")
        return

    # Анализ результатов
    print("\n" + "=" * 70)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 70)

    if len(satellite.history['t']) > 10:
        # Вывод статистики
        print(f"\nСТАТИСТИКА:")
        print(f"  • Время симуляции: {satellite.time / 3600:.2f} ч")
        print(f"  • Начальная высота: {satellite.history['altitude'][0] / 1000:.1f} км")
        print(f"  • Конечная высота: {satellite.history['altitude'][-1] / 1000:.1f} км")
        print(
            f"  • Потеря высоты: {(satellite.history['altitude'][0] - satellite.history['altitude'][-1]) / 1000:.2f} км")
        print(
            f"  • Средняя скорость снижения: {(satellite.history['altitude'][0] - satellite.history['altitude'][-1]) / satellite.time * 1000:.3f} м/с")

        # Построение графиков
        print("\nПостроение графиков...")
        try:
            plot_results(satellite)
        except Exception as e:
            print(f"Ошибка при построении графиков: {e}")
            print("Для построения графиков установите matplotlib: pip install matplotlib")
    else:
        print("Недостаточно данных для анализа")

    print("\n" + "=" * 70)
    print("МОДЕЛИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 70)


if __name__ == "__main__":
    main()