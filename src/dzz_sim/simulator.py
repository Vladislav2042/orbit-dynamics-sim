import pygame
import numpy as np
import config as cfg


class Simulator:
    """Визуализация ДЗЗ-спутника на НОО с видом сверху на плоскость XY"""

    def __init__(self, satellite):
        self.satellite = satellite
        self.running = True
        self.paused = False

        # Инициализация PyGame
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Модель ДЗЗ-спутника на НОО")
        self.clock = pygame.time.Clock()

        # ЯРКИЕ ЦВЕТА ДЛЯ ВИЗУАЛИЗАЦИИ
        self.colors = {
            'background': (0, 0, 0),  # Черный фон
            'earth': (30, 70, 200),  # Синяя Земля
            'earth_outline': (100, 150, 255),  # Светло-синий контур
            'orbit_ideal': (255, 50, 50),  # ЯРКО-КРАСНАЯ идеальная орбита
            'orbit_real': (50, 255, 50),  # ЯРКО-ЗЕЛЕНАЯ реальная орбита
            'satellite': (255, 255, 0),  # ЯРКО-ЖЕЛТЫЙ спутник
            'satellite_inner': (255, 200, 0),  # Оранжевый центр
            'text': (255, 255, 255),  # Белый текст
            'grid': (50, 50, 100),  # Темно-синяя сетка
            'velocity_vector': (255, 100, 100),  # Светло-красный вектор
            'velocity_tip': (255, 0, 0),  # Красный кончик
            'atmosphere_light': (80, 120, 220),  # Светло-голубой
            'atmosphere_dark': (40, 80, 180),  # Темно-голубой
            'continents': (30, 180, 30),  # Зеленые континенты
            'scan_line': (200, 200, 255),  # Голубые линии ДЗЗ
            'legend_bg': (20, 20, 40),  # Темно-синий фон панелей
            'legend_border': (80, 100, 200)  # Синяя рамка
        }

        # Параметры визуализации
        self.center = (600, 400)
        self.scale = cfg.SCALE_FACTOR * 2000
        self.earth_radius_px = cfg.EARTH_RADIUS_PX

        # Траектория спутника
        self.trajectory = []
        self.max_trajectory_points = 2000

        # Шрифты
        try:
            self.font_small = pygame.font.SysFont('Arial', 14, bold=True)
            self.font_medium = pygame.font.SysFont('Arial', 18, bold=True)
            self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
        except:
            self.font_small = pygame.font.Font(None, 16)
            self.font_medium = pygame.font.Font(None, 20)
            self.font_large = pygame.font.Font(None, 28)

        # Информационные панели
        self.panels = {
            'orbit': pygame.Rect(20, 20, 350, 180),
            'physics': pygame.Rect(20, 220, 350, 200),
            'atmosphere': pygame.Rect(20, 440, 350, 150),
            'legend': pygame.Rect(830, 20, 350, 220),
            'dzz': pygame.Rect(400, 20, 400, 120)  # Панель ДЗЗ
        }

        # Инициализация данных
        self.last_info_update = 0
        self.info_update_interval = 0.5
        self.orbit_content = ["Загрузка..."]
        self.physics_content = ["Загрузка..."]
        self.atmosphere_content = ["Загрузка..."]
        self.dzz_content = ["Данные ДЗЗ..."]

    def world_to_screen(self, world_x, world_y):
        """Преобразование мировых координат в экранные"""
        screen_x = self.center[0] + world_x * self.scale
        screen_y = self.center[1] - world_y * self.scale  # Инвертируем ось Y
        return int(screen_x), int(screen_y)

    def draw_earth(self):
        """Отрисовка Земли с атмосферными слоями"""
        # Атмосферные слои
        pygame.draw.circle(self.screen, self.colors['atmosphere_light'],
                           self.center, self.earth_radius_px + 40)
        pygame.draw.circle(self.screen, self.colors['atmosphere_dark'],
                           self.center, self.earth_radius_px + 20)

        # Земля
        pygame.draw.circle(self.screen, self.colors['earth'],
                           self.center, self.earth_radius_px)
        pygame.draw.circle(self.screen, self.colors['earth_outline'],
                           self.center, self.earth_radius_px, 3)

        # Континенты
        for i in range(6):
            angle = 2 * np.pi * i / 6 + pygame.time.get_ticks() / 15000
            distance = self.earth_radius_px * 0.7
            x = self.center[0] + int(np.cos(angle) * distance)
            y = self.center[1] + int(np.sin(angle) * distance)
            size = 12 + i * 2
            pygame.draw.circle(self.screen, self.colors['continents'], (x, y), size)

    def draw_ideal_orbit(self):
        """Отрисовка идеальной круговой орбиты КРАСНЫМ цветом"""
        points = []
        num_points = 150

        for i in range(num_points + 1):
            angle = 2 * np.pi * i / num_points
            x = cfg.ORBIT_RADIUS * np.cos(angle)
            y = cfg.ORBIT_RADIUS * np.sin(angle)
            sx, sy = self.world_to_screen(x, y)
            points.append((sx, sy))

        # Толстая КРАСНАЯ линия
        if len(points) > 1:
            pygame.draw.lines(self.screen, self.colors['orbit_ideal'],
                              False, points, 3)

    def draw_satellite(self):
        """Отрисовка спутника и его траектории"""
        x, y, z = self.satellite.state[:3]
        sx, sy = self.world_to_screen(x, y)

        # Сохранение траектории
        self.trajectory.append((sx, sy))
        if len(self.trajectory) > self.max_trajectory_points:
            self.trajectory.pop(0)

        # ЗЕЛЕНАЯ траектория
        if len(self.trajectory) > 2:
            pygame.draw.lines(self.screen, self.colors['orbit_real'],
                              False, self.trajectory, 2)

        # Спутник - ЯРКО-ЖЕЛТЫЙ с оранжевым центром
        pygame.draw.circle(self.screen, self.colors['satellite'], (sx, sy), 10)
        pygame.draw.circle(self.screen, self.colors['satellite_inner'], (sx, sy), 6)
        pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), 2)

        # Свечение спутника
        for radius in [15, 20, 25]:
            glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 100, 30),
                               (radius, radius), radius)
            self.screen.blit(glow_surface, (sx - radius, sy - radius))

        # Вектор скорости
        vx, vy, vz = self.satellite.state[3:]
        speed = np.sqrt(vx ** 2 + vy ** 2)

        if speed > 100:
            vector_length = min(80, speed * 0.08)
            end_x = sx + int(vx / speed * vector_length)
            end_y = sy - int(vy / speed * vector_length)

            # Основная линия вектора
            pygame.draw.line(self.screen, self.colors['velocity_vector'],
                             (sx, sy), (end_x, end_y), 3)

            # Стрелка
            angle = np.arctan2(sy - end_y, end_x - sx)
            arrow_size = 8
            left_x = end_x - int(arrow_size * np.cos(angle + np.pi / 6))
            left_y = end_y + int(arrow_size * np.sin(angle + np.pi / 6))
            right_x = end_x - int(arrow_size * np.cos(angle - np.pi / 6))
            right_y = end_y + int(arrow_size * np.sin(angle - np.pi / 6))

            pygame.draw.line(self.screen, self.colors['velocity_tip'],
                             (end_x, end_y), (left_x, left_y), 3)
            pygame.draw.line(self.screen, self.colors['velocity_tip'],
                             (end_x, end_y), (right_x, right_y), 3)

        # Линии зондирования ДЗЗ
        for i in range(5):
            scan_length = 60
            scan_angle = i * np.pi / 10 + pygame.time.get_ticks() / 5000
            scan_x = sx + int(scan_length * np.cos(scan_angle))
            scan_y = sy + int(scan_length * np.sin(scan_angle))
            pygame.draw.line(self.screen, self.colors['scan_line'],
                             (sx, sy), (scan_x, scan_y), 1)

    def draw_info_panel(self, rect, title, content, title_color=None):
        """Отрисовка информационной панели"""
        if title_color is None:
            title_color = (200, 200, 255)

        # Фон панели
        panel = pygame.Surface((rect.width, rect.height))
        panel.fill(self.colors['legend_bg'])
        panel.set_alpha(230)
        self.screen.blit(panel, rect)

        # Рамка
        pygame.draw.rect(self.screen, self.colors['legend_border'], rect, 2)

        # Заголовок
        if title:
            title_text = self.font_medium.render(title, True, title_color)
            self.screen.blit(title_text, (rect.x + 10, rect.y + 10))

        # Содержимое
        y_offset = 40 if title else 10
        for line in content:
            text = self.font_small.render(line, True, self.colors['text'])
            self.screen.blit(text, (rect.x + 15, rect.y + y_offset))
            y_offset += 22

    def update_info(self):
        """Обновление информации на панелях"""
        current_time = pygame.time.get_ticks() / 1000.0

        if current_time - self.last_info_update > self.info_update_interval:
            self.last_info_update = current_time

            # Текущие параметры
            pos = self.satellite.state[:3]
            vel = self.satellite.state[3:]
            altitude = (np.linalg.norm(pos) - cfg.R_EARTH) / 1000
            velocity = np.linalg.norm(vel) / 1000
            elements = self.satellite.orbital_elements

            # Орбитальные параметры
            self.orbit_content = [
                f"Высота: {altitude:.1f} км",
                f"Скорость: {velocity:.3f} км/с",
                f"Период: {elements['period'] / 60:.1f} мин",
                f"Эксцентриситет: {elements['eccentricity']:.6f}",
                f"Большая полуось: {elements['semi_major_axis'] / 1000:.1f} км",
                f"Энергия: {elements['energy'] / 1e6:.2f} МДж/кг"
            ]

            # Физические параметры
            time_hours = self.satellite.time / 3600
            self.physics_content = [
                f"Время моделирования: {time_hours:.2f} ч",
                f"Координаты: X={pos[0] / 1000:.0f} км",
                f"           Y={pos[1] / 1000:.0f} км",
                f"           Z={pos[2] / 1000:.0f} км",
                f"Шаг интегрирования: {cfg.TIME_STEP} с",
                f"Масса спутника: {self.satellite.mass} кг",
                f"Площадь сечения: {self.satellite.cross_section} м²"
            ]

            # Атмосферные параметры
            density = self.satellite.atmospheric_density(altitude * 1000)
            drag_force = 0.5 * density * cfg.DRAG_COEFF * self.satellite.cross_section * (velocity * 1000) ** 2
            self.atmosphere_content = [
                f"Плотность атмосферы: {density:.2e} кг/м³",
                f"Сила сопротивления: {drag_force:.1f} Н",
                f"Ускорение от drag: {drag_force / self.satellite.mass:.2e} м/с²",
                f"Высота шкалы: {cfg.H_SCALE / 1000:.1f} км",
                f"Коэффициент Cd: {cfg.DRAG_COEFF}"
            ]

            # Данные ДЗЗ
            self.dzz_content = [
                "ДАННЫЕ ДЗЗ-СПУТНИКА:",
                f"Тип орбиты: Солнечно-синхронная",
                f"Наклонение: 97.7°",
                f"Повторяемость: 16 суток",
                f"Полоса съемки: 290 км",
                f"Разрешение: 10-30 м",
                f"Спектральные каналы: 13"
            ]

    def draw_hud(self):
        """Отрисовка всей информации"""
        self.update_info()

        # Основные панели
        self.draw_info_panel(self.panels['orbit'], "ОРБИТАЛЬНЫЕ ПАРАМЕТРЫ", self.orbit_content)
        self.draw_info_panel(self.panels['physics'], "ФИЗИЧЕСКИЕ ПАРАМЕТРЫ", self.physics_content)
        self.draw_info_panel(self.panels['atmosphere'], "АТМОСФЕРА", self.atmosphere_content)
        self.draw_info_panel(self.panels['dzz'], "СПУТНИК ДЗЗ", self.dzz_content, (255, 200, 100))

        # Легенда
        legend_content = [
            "ЛЕГЕНДА:",
            "🔵 Синий круг - Земля",
            "🔴 КРАСНАЯ линия - идеальная орбита",
            "🟢 ЗЕЛЕНАЯ линия - реальная траектория",
            "🟡 ЖЕЛТАЯ точка - спутник",
            "🔴 Красная стрелка - вектор скорости",
            "🔵 Голубые линии - зондирование ДЗЗ",
            "",
            "УПРАВЛЕНИЕ:",
            "ESC - выход из программы",
            "ПРОБЕЛ - пауза/продолжение",
            "+/- - изменение масштаба",
            "R - сброс масштаба"
        ]
        self.draw_info_panel(self.panels['legend'], "", legend_content)

        # Индикатор паузы
        if self.paused:
            pause_surface = pygame.Surface((200, 60))
            pause_surface.fill((0, 0, 0))
            pause_surface.set_alpha(180)
            self.screen.blit(pause_surface, (500, 300))

            pause_text = self.font_large.render("ПАУЗА", True, (255, 100, 100))
            self.screen.blit(pause_text, (1200 // 2 - pause_text.get_width() // 2, 320))

    def draw_grid(self):
        """Отрисовка координатной сетки"""
        grid_color = self.colors['grid']
        center_x, center_y = self.center

        # Вертикальные линии
        for x in range(-5, 6):
            screen_x = center_x + x * 100
            pygame.draw.line(self.screen, grid_color,
                             (screen_x, center_y - 500),
                             (screen_x, center_y + 500), 1)

        # Горизонтальные линии
        for y in range(-5, 6):
            screen_y = center_y + y * 100
            pygame.draw.line(self.screen, grid_color,
                             (center_x - 500, screen_y),
                             (center_x + 500, screen_y), 1)

        # Центр
        pygame.draw.circle(self.screen, (255, 255, 255), self.center, 3)

    def draw(self):
        """Основной метод отрисовки"""
        # Черный фон
        self.screen.fill(self.colors['background'])

        # Сетка
        self.draw_grid()

        # Объекты (в порядке удаления от наблюдателя)
        self.draw_ideal_orbit()  # 1. Красная орбита
        self.draw_earth()  # 2. Земля
        self.draw_satellite()  # 3. Спутник и траектория

        # Информация
        self.draw_hud()

        # Заголовок
        title = self.font_large.render("МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ДЗЗ-СПУТНИКА НА НОО",
                                       True, (255, 255, 200))
        self.screen.blit(title, (1200 // 2 - title.get_width() // 2, 750))

        # Обновление экрана
        pygame.display.flip()

    def run(self):
        """Основной цикл симуляции"""
        print("=" * 60)
        print("ЗАПУСК МОДЕЛИ ДЗЗ-СПУТНИКА НА НОО")
        print("=" * 60)
        print(f"Начальная высота: {cfg.LEO_HEIGHT / 1000:.0f} км")
        print(f"Начальная скорость: {cfg.ORBITAL_VELOCITY / 1000:.3f} км/с")
        print("=" * 60)

        while self.running and self.satellite.time < cfg.SIMULATION_DURATION:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        print(f"{'ПАУЗА' if self.paused else 'ПРОДОЛЖЕНИЕ'}")
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.scale *= 1.2
                        print(f"Масштаб увеличен: {self.scale:.2e}")
                    elif event.key == pygame.K_MINUS:
                        self.scale /= 1.2
                        print(f"Масштаб уменьшен: {self.scale:.2e}")
                    elif event.key == pygame.K_r:
                        self.scale = cfg.SCALE_FACTOR * 2000
                        print(f"Масштаб сброшен: {self.scale:.2e}")

            # Обновление физики (если не на паузе)
            if not self.paused:
                if not self.satellite.update():
                    print("Спутник вошел в атмосферу!")
                    break

            # Отрисовка
            self.draw()

            # Ограничение FPS
            self.clock.tick(60)

        # Завершение
        self.quit_simulation()

    def quit_simulation(self):
        """Корректное завершение"""
        print("=" * 60)
        print(f"СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print(f"Итоговое время: {self.satellite.time / 3600:.2f} ч")
        print("=" * 60)
        pygame.quit()