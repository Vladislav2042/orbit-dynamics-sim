import numpy as np
from skyfield.api import load, wgs84
from scipy.spatial.transform import Rotation as R
import pyvista as pv
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime as dt_datetime
import itertools
import asyncio
from playwright.async_api import async_playwright
import traceback


# ==================== ИСПРАВЛЕННАЯ ФУНКЦИЯ get_nadir_vector_global ====================
def get_nadir_vector_global(satellite_object, time_val):
    """
    ПРАВИЛЬНЫЙ расчёт направления на надир.
    Использует относительную позицию спутника относительно центра Земли,
    а не абсолютную позицию в Солнечной системе.
    Это решает проблему коллинеарности векторов Солнце/надир.
    """
    try:
        # Относительная позиция спутника относительно центра Земли (в км)
        sat_pos_relative_km = satellite_object.at(time_val).position.km - earth.at(time_val).position.km
        norm = np.linalg.norm(sat_pos_relative_km)
        if norm < 1e-6:
            print("ПРЕДУПРЕЖДЕНИЕ: спутник слишком близко к центру Земли в расчётах.")
            return np.array([0.0, 0.0, -1.0])
        return -sat_pos_relative_km / norm
    except Exception as e:
        print(f"ОШИБКА в get_nadir_vector_global: {e}")
        return np.array([0.0, 0.0, -1.0])


# ==================== УЛУЧШЕННАЯ ФУНКЦИЯ ДЛЯ PLAYWRIGHT ====================
async def get_coordinates_with_playwright(url_target='https://r4uab.ru/satdb/cubesx-sirius-hse/'):
    """
    Улучшенная версия с большими таймаутами и лучшей обработкой ошибок.
    """
    print("Playwright: Запуск для получения координат (улучшенная версия)...")
    lat_val, lon_val, alt_val = None, None, None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']  # чуть меньше детекции
            )
            page = await browser.new_page()
            
            # Увеличили таймауты
            await page.goto(url_target, timeout=60000, wait_until="domcontentloaded")
            
            iframe_selector = 'iframe[src="https://r4uab.ru/content/modules/sattrack/?catalog_number=47951"]'
            print(f"Playwright: Ожидание iframe...")
            
            try:
                await page.wait_for_selector(iframe_selector, state='visible', timeout=30000)
                iframe_element = await page.query_selector(iframe_selector)
            except Exception as e_iframe_wait:
                print(f"Playwright: Iframe не найден или не загрузился: {e_iframe_wait}")
                iframe_element = None

            if iframe_element:
                print("Playwright: Iframe найден. Переходим внутрь...")
                frame = await iframe_element.content_frame()
                if frame:
                    await frame.wait_for_selector('#data_panel', state='visible', timeout=30000)
                    print("Playwright: #data_panel найдена.")

                    raw_latitude_text = await frame.inner_text('.latitude')
                    raw_longitude_text = await frame.inner_text('.longitude')
                    raw_altitude_text = await frame.inner_text('.altitude')

                    print(f"Playwright: Сырые данные: Lat='{raw_latitude_text}', Lon='{raw_longitude_text}', Alt='{raw_altitude_text}'")
                    
                    latitude_text = raw_latitude_text.replace("Lat:", "").strip()
                    longitude_text = raw_longitude_text.replace("Lng:", "").strip()
                    altitude_text = raw_altitude_text.replace("Alt:", "").strip()

                    match_lat = re.search(r"(\d+)°\s*([\d.]+)[′']\s*([NS])", latitude_text)
                    if match_lat:
                        deg, minute, direction = match_lat.groups()
                        lat_val = float(deg) + float(minute) / 60.0
                        if direction == 'S':
                            lat_val *= -1

                    match_lon = re.search(r"(\d+)°\s*([\d.]+)[′']\s*([EW])", longitude_text)
                    if match_lon:
                        deg, minute, direction = match_lon.groups()
                        lon_val = float(deg) + float(minute) / 60.0
                        if direction == 'W':
                            lon_val *= -1

                    match_alt = re.search(r"([\d.]+)\s*км", altitude_text)
                    if match_alt:
                        alt_val = float(match_alt.group(1))

                    if lat_val is not None and lon_val is not None and alt_val is not None:
                        print(f"Playwright: Успешно извлечены координаты: Lat={lat_val:.3f}, Lon={lon_val:.3f}, Alt={alt_val:.3f}")
                    else:
                        print("Playwright: Не удалось распарсить все координаты.")
                else:
                    print("Playwright: Не удалось получить content_frame().")
            else:
                print("Playwright: Iframe не найден по селектору.")
            
            await browser.close()
    except Exception as e:
        print(f"Playwright: Общая ошибка - {e}")
        print("Подсказка: сайт может блокировать автоматизацию или медленно работать.")
    return lat_val, lon_val, alt_val


# ==================== УЛУЧШЕННЫЙ БЛОК ПОЛУЧЕНИЯ ТЕЛЕМЕТРИИ ====================
print("=== Запрос данных телеметрии с сайта r4uab.ru ===")
url_telemetry = "https://r4uab.ru/satdb/cubesx-sirius-hse/"
headers_bs4 = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

Time_value = None
Date_TLM = None
electricity1 = electricity2 = electricity3 = None

try:
    response_bs4 = requests.get(url_telemetry, headers=headers_bs4, timeout=20)
    response_bs4.raise_for_status()
    soup_bs4 = BeautifulSoup(response_bs4.text, 'html.parser')
    content_price_blocks = soup_bs4.find_all('div', class_='content_price_nov')
    
    for block in content_price_blocks:
        header_div = block.find('div', class_='name_price_nov')
        value_span_container = block.find('div', class_='price_opisanie')
        if header_div and value_span_container:
            value_span = value_span_container.find('span')
            if value_span:
                header_text = header_div.get_text(strip=True)
                value_text = value_span.get_text(strip=True)
                if 'Время ТЛМ' == header_text:
                    Time_value = value_text
                elif 'Дата ТЛМ' == header_text:
                    Date_TLM = value_text
                elif 'Ток СБ №1' == header_text:
                    electricity1 = value_text
                elif 'Ток СБ №2' == header_text:
                    electricity2 = value_text
                elif 'Ток СБ №3' == header_text:
                    electricity3 = value_text

    if Date_TLM and Time_value:
        print(f"Телеметрия успешно получена: Дата={Date_TLM}, Время={Time_value}")
    else:
        print("Предупреждение: Не все поля телеметрии найдены на сайте.")

except requests.exceptions.SSLError as e:
    print("КРИТИЧЕСКАЯ ОШИБКА SSL при подключении к r4uab.ru")
    print("Возможные причины:")
    print("  - Устаревшие сертификаты в твоём окружении Anaconda")
    print("  - Корпоративный прокси/файрвол")
    print("  - Проблемы на стороне сайта")
    print("Решение: попробуй запустить скрипт в обычном Python (не Anaconda) или обнови certifi:")
    print("   pip install --upgrade certifi")
except requests.exceptions.RequestException as e:
    print(f"Ошибка сети при запросе телеметрии: {e}")
except Exception as e:
    print(f"Неожиданная ошибка при парсинге телеметрии: {e}")


# ==================== ВРЕМЯ ====================
ts = load.timescale()
print("\nЗагрузка эфемерид Skyfield...")
eph = load('de421.bsp')
earth = eph['earth']
sun = eph['sun']
print("Эфемериды загружены.")

time_utc = None
if Date_TLM and Time_value:
    try:
        clean_date_str = Date_TLM.replace(" г.", "").strip()
        clean_time_str = Time_value.replace(" UTC", "").strip()
        dt_obj = dt_datetime.strptime(f"{clean_date_str} {clean_time_str}", "%d.%m.%Y %H:%M:%S")
        time_utc = ts.utc(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, dt_obj.second)
        print(f"Используется время из телеметрии: {time_utc.utc_iso()}")
    except Exception as e:
        print(f"Ошибка парсинга времени из телеметрии: {e}")

if time_utc is None:
    time_utc = ts.now()
    print(f"ВНИМАНИЕ: Используется ТЕКУЩЕЕ время UTC: {time_utc.utc_iso()}")


# ==================== ПОЛУЧЕНИЕ КООРДИНАТ ====================
print("\n=== Получение координат спутника ===")
sat_lat_deg_pw, sat_lon_deg_pw, sat_alt_km_pw = None, None, None

try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sat_lat_deg_pw, sat_lon_deg_pw, sat_alt_km_pw = loop.run_until_complete(
        get_coordinates_with_playwright()
    )
except Exception as e:
    print(f"Ошибка запуска Playwright: {e}")

if sat_lat_deg_pw is not None and sat_lon_deg_pw is not None and sat_alt_km_pw is not None:
    sat_lat_deg = sat_lat_deg_pw
    sat_lon_deg = sat_lon_deg_pw
    sat_alt_km = sat_alt_km_pw
    print(f"Координаты получены автоматически: Lat={sat_lat_deg:.3f}, Lon={sat_lon_deg:.3f}, Alt={sat_alt_km:.3f} км")
else:
    print("\n>>> Не удалось получить координаты автоматически. Введите вручную <<<")
    def get_float_input(prompt_text, default_val):
        while True:
            try:
                val = input(f"{prompt_text} (по умолчанию {default_val}): ").strip()
                if val == "":
                    return default_val
                return float(val.replace(',', '.'))
            except ValueError:
                print("Ошибка: введите число.")

    sat_lat_deg = get_float_input("Широта (южная - отрицательная)", -44.674)
    sat_lon_deg = get_float_input("Долгота (восточная)", 349.343)
    sat_alt_km  = get_float_input("Высота над Землёй (км)", 312.662)


# ==================== ТОКИ ПАНЕЛЕЙ ====================
def parse_current_value(current_str, default_val_amps=0.001):
    if current_str is None:
        return default_val_amps
    current_str = current_str.strip().lower()
    try:
        match = re.search(r"([-+]?\d*\.?\d+)", current_str)
        if match:
            val = float(match.group(1))
            if "ма" in current_str or "мa" in current_str:
                val /= 1000.0
            elif "a" not in current_str and "а" not in current_str and abs(val) > 1.0:
                val /= 1000.0
            return val
    except:
        pass
    return default_val_amps


I_sb_current = {
    1: parse_current_value(electricity1, 0.001),
    2: parse_current_value(electricity2, 0.001),
    3: parse_current_value(electricity3, 0.001)
}
print(f"\nТоки солнечных батарей (А): {I_sb_current}")

if all(abs(v) < 0.01 for v in I_sb_current.values()):
    print("ВНИМАНИЕ: Токи очень маленькие. Рекомендуется ввести реальные значения токов вручную для точности.")
    I_sb_current[1] = get_float_input("Ток СБ №1 (А)", 0.045)
    I_sb_current[2] = get_float_input("Ток СБ №2 (А)", 0.038)
    I_sb_current[3] = get_float_input("Ток СБ №3 (А)", 0.052)


# ==================== КОНСТАНТЫ (ЗАПОЛНИ СВОИ ЗНАЧЕНИЯ!) ====================
I_max_panel = {1: 0.15, 2: 0.15, 3: 0.15}          # ← ЗАПОЛНИ РЕАЛЬНЫЕ МАКСИМАЛЬНЫЕ ТОКИ
satellite_dimensions = np.array([0.1, 0.1, 0.2])   # ← РАЗМЕРЫ СПУТНИКА В МЕТРАХ
NADIR_POINTING_AXIS_BODY = np.array([0.0, 0.0, 1.0])

default_n_panel_body_for_calc = {
    1: np.array([1.0, 0.0, 0.0]),
    2: np.array([0.0, 1.0, 0.0]),
    3: np.array([0.0, 0.0, 1.0])
}

satellite_sky_obj = earth + wgs84.latlon(
    latitude_degrees=sat_lat_deg,
    longitude_degrees=sat_lon_deg,
    elevation_m=sat_alt_km * 1000
)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def solve_sun_vector_body(I_sb_current_vals, I_max_panel_vals, n_panels_body_map_vals):
    cos_alphas = {}
    for panel_id, n_vec in n_panels_body_map_vals.items():
        if panel_id in I_sb_current_vals and panel_id in I_max_panel_vals:
            if I_max_panel_vals[panel_id] < 1e-6:
                cos_alpha = 0.0
            else:
                cos_alpha = min(max(I_sb_current_vals[panel_id] / I_max_panel_vals[panel_id], -1.0), 1.0)
            cos_alphas[panel_id] = cos_alpha
        else:
            cos_alphas[panel_id] = 0.0

    s_sun_body_unnormalized = np.zeros(3)
    for panel_id, n_vec_panel in n_panels_body_map_vals.items():
        if panel_id in cos_alphas:
            s_sun_body_unnormalized += n_vec_panel * cos_alphas[panel_id]

    norm = np.linalg.norm(s_sun_body_unnormalized)
    if norm < 1e-9:
        return np.array([1.0, 0.0, 0.0])
    return s_sun_body_unnormalized / norm


def get_sun_vector_global(satellite_object, time_val):
    astrometric = satellite_object.at(time_val).observe(sun)
    s_sun_global_unnormalized = astrometric.position.km
    norm = np.linalg.norm(s_sun_global_unnormalized)
    if norm < 1e-9:
        return np.array([1.0, 0.0, 0.0])
    return s_sun_global_unnormalized / norm


def calculate_attitude_triad(v1_body_vec, v2_body_vec, v1_global_vec, v2_global_vec):
    v1_b = v1_body_vec / np.linalg.norm(v1_body_vec)
    v2_b = v2_body_vec / np.linalg.norm(v2_body_vec)
    v1_g = v1_global_vec / np.linalg.norm(v1_global_vec)
    v2_g = v2_global_vec / np.linalg.norm(v2_global_vec)

    if np.abs(np.dot(v1_b, v2_b)) > 0.999 or np.abs(np.dot(v1_g, v2_g)) > 0.999:
        raise ValueError("Векторы коллинеарны — TRIAD не может быть применён.")

    t1_b = v1_b
    t2_b = np.cross(v1_b, v2_b)
    t2_b /= np.linalg.norm(t2_b)
    t3_b = np.cross(t1_b, t2_b)
    M_body = np.array([t1_b, t2_b, t3_b]).T

    t1_g = v1_g
    t2_g = np.cross(v1_g, v2_g)
    t2_g /= np.linalg.norm(t2_g)
    t3_g = np.cross(t1_g, t2_g)
    M_global = np.array([t1_g, t2_g, t3_g]).T

    rotation_matrix = np.dot(M_global, M_body.T)
    return rotation_matrix


# ==================== ОСНОВНЫЕ РАСЧЁТЫ ====================
print(f"\nВремя расчётов: {time_utc.utc_iso()}")

sat_pos_gcrs_km = satellite_sky_obj.at(time_utc).position.km
s_sun_global = get_sun_vector_global(satellite_sky_obj, time_utc)
nadir_global = get_nadir_vector_global(satellite_sky_obj, time_utc)
nadir_body_assumed = NADIR_POINTING_AXIS_BODY / np.linalg.norm(NADIR_POINTING_AXIS_BODY)

print(f"Позиция КА (относительно Земли): {np.linalg.norm(sat_pos_gcrs_km - earth.at(time_utc).position.km):.1f} км от центра")

# --- Поиск лучшей гипотезы ---
print("\n=== Поиск наилучшей гипотезы расположения солнечных панелей ===")

possible_normals_map = {
    "+X": np.array([1.0, 0.0, 0.0]), "-X": np.array([-1.0, 0.0, 0.0]),
    "+Y": np.array([0.0, 1.0, 0.0]), "-Y": np.array([0.0, -1.0, 0.0]),
    "+Z": np.array([0.0, 0.0, 1.0]), "-Z": np.array([0.0, 0.0, -1.0])
}
face_names_ordered = list(possible_normals_map.keys())
panel_ids_ordered = sorted(I_sb_current.keys())

best_hypothesis_info = None
max_consistency_score = -2.0

for face_indices in itertools.permutations(range(len(face_names_ordered)), len(panel_ids_ordered)):
    current_n_panel = {}
    hypothesis_desc = []
    for i, panel_id in enumerate(panel_ids_ordered):
        face_name = face_names_ordered[face_indices[i]]
        current_n_panel[panel_id] = possible_normals_map[face_name]
        hypothesis_desc.append(f"СБ{panel_id}→{face_name}")

    try:
        s_sun_body_hyp = solve_sun_vector_body(I_sb_current, I_max_panel, current_n_panel)
        if np.linalg.norm(s_sun_body_hyp) < 1e-6:
            continue

        attitude_hyp = calculate_attitude_triad(s_sun_body_hyp, nadir_body_assumed, s_sun_global, nadir_global)
        
        s_sun_transformed = attitude_hyp.T @ s_sun_global
        s_sun_transformed /= np.linalg.norm(s_sun_transformed)
        
        score = np.dot(s_sun_body_hyp, s_sun_transformed)
        
        if score > max_consistency_score:
            max_consistency_score = score
            best_hypothesis_info = {
                'name': "; ".join(hypothesis_desc),
                'config': current_n_panel,
                'attitude': attitude_hyp,
                's_sun_body': s_sun_body_hyp,
                'score': score
            }
    except ValueError:
        continue

print(f"Проверено гипотез: {len(list(itertools.permutations(range(6), 3)))}")

# ==================== ФИНАЛЬНАЯ ОРИЕНТАЦИЯ ====================
attitude_matrix = np.identity(3)
s_sun_body = np.array([1.0, 0.0, 0.0])
n_panel_body_for_calc_final = default_n_panel_body_for_calc

if best_hypothesis_info:
    print(f"\n>>> ЛУЧШАЯ ГИПОТЕЗА: {best_hypothesis_info['name']} (score={best_hypothesis_info['score']:.4f})")
    attitude_matrix = best_hypothesis_info['attitude']
    s_sun_body = best_hypothesis_info['s_sun_body']
    n_panel_body_for_calc_final = best_hypothesis_info['config']
else:
    print("\nПРЕДУПРЕЖДЕНИЕ: Хорошая гипотеза не найдена. Используется конфигурация по умолчанию.")
    s_sun_body = solve_sun_vector_body(I_sb_current, I_max_panel, n_panel_body_for_calc_final)
    try:
        attitude_matrix = calculate_attitude_triad(s_sun_body, nadir_body_assumed, s_sun_global, nadir_global)
    except ValueError as e:
        print(f"TRIAD не сработал даже с дефолтной конфигурацией: {e}")
        print("Будет использована единичная матрица (ориентация неизвестна).")

# Вывод результатов
print("\n=== Финальные результаты ===")
print(f"Позиция КА в GCRS [км]: {sat_pos_gcrs_km}")
print(f"Вектор на Солнце (глобальный): {s_sun_global}")
print(f"Вектор на надир (глобальный): {nadir_global}")
print(f"Вектор на Солнце (в СК КА): {s_sun_body}")
print(f"Матрица ориентации (body → global):\n{attitude_matrix}")

orientation_quat = R.from_matrix(attitude_matrix).as_quat()
orientation_euler = R.from_matrix(attitude_matrix).as_euler('xyz', degrees=True)
print(f"Кватернион (XYZW): {orientation_quat}")
print(f"Углы Эйлера XYZ [°]: Roll={orientation_euler[0]:.2f}, Pitch={orientation_euler[1]:.2f}, Yaw={orientation_euler[2]:.2f}")

# ==================== 3D ВИЗУАЛИЗАЦИЯ ====================
plotter = pv.Plotter(window_size=[1000, 700], lighting="light_kit")
plotter.background_color = 'black'

# Корпус спутника
body_mesh = pv.Box(bounds=[
    -satellite_dimensions[0]/2, satellite_dimensions[0]/2,
    -satellite_dimensions[1]/2, satellite_dimensions[1]/2,
    -satellite_dimensions[2]/2, satellite_dimensions[2]/2
])
body_actor = plotter.add_mesh(body_mesh, color='red', show_edges=True, line_width=2)

rotation_transform = np.eye(4)
rotation_transform[:3, :3] = attitude_matrix
body_actor.user_matrix = rotation_transform

# Оси
axis_len = np.max(satellite_dimensions) * 1.8
plotter.add_arrows([0,0,0], attitude_matrix @ [axis_len,0,0], color='darkred', label="X_КА")
plotter.add_arrows([0,0,0], attitude_matrix @ [0,axis_len,0], color='darkgreen', label="Y_КА")
plotter.add_arrows([0,0,0], attitude_matrix @ [0,0,axis_len], color='darkblue', label="Z_КА")

# Солнечные панели
if n_panel_body_for_calc_final:
    for panel_id, normal in n_panel_body_for_calc_final.items():
        panel_mesh = pv.Box(bounds=[-0.045, 0.045, -0.045, 0.045, -0.01, 0.01])
        # Простое смещение панели
        offset = normal * (satellite_dimensions[2]/2 * 1.05)
        panel_mesh.translate(offset, inplace=True)
        panel_actor = plotter.add_mesh(panel_mesh, color='deepskyblue', show_edges=True)
        panel_actor.user_matrix = rotation_transform

# Стрелки
arrow_scale = np.max(satellite_dimensions) * 6
plotter.add_arrows([0,0,0], attitude_matrix @ s_sun_body, mag=arrow_scale, color='yellow', label="Направление на Солнце")
plotter.add_arrows([0,0,0], attitude_matrix @ nadir_body_assumed, mag=arrow_scale, color='purple', label="Направление на надир (Z)")

plotter.add_legend()
plotter.camera.position = [0, -15, 8]
plotter.camera.focal_point = [0, 0, 0]
plotter.show()

print("\nСкрипт завершён.")