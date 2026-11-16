# Orbit Dynamics Simulator

Spacecraft motion and orbit determination in Python — two independent projects kept in one toolkit:

1. **LEO Earth-observation satellite simulator** — propagation of the full 6-DOF state vector with a
   point-mass gravity field plus the J2 zonal harmonic, an exponential atmosphere, aerodynamic drag and
   atmosphere rotation, integrated numerically and rendered live in a Pygame window.
2. **Satellite positioning from ephemerides** — Skyfield with the JPL DE421 ephemeris, orbit orientation
   via rotation matrices, a 3D scene in PyVista, and live tracker coordinates scraped with Playwright.

Both are university coursework projects, cleaned up for publication. Code comments are in Russian
(original), README in English.

## Physics

### `src/dzz_sim/` — LEO remote-sensing satellite

| Model | Implementation |
|---|---|
| Gravity | point mass `μ = 3.986·10¹⁴ m³/s²` + J2 zonal harmonic `J2 = 1.08263·10⁻³` |
| Atmosphere | exponential, `ρ = ρ₀·exp(−h/H)`, `ρ₀ = 1.225 kg/m³`, `H = 8.5 km` (a thinner branch takes over above 100 km) |
| Drag | `a_drag = −½·ρ·v²·C_d·A/m`, `C_d = 2.2` |
| Atmosphere rotation | velocity taken relative to the rotating atmosphere, `ω⊕ = 7.292115·10⁻⁵ rad/s` |
| Integrator | classical Runge–Kutta 4, `dt = 10 s`, 24 h of simulated time |
| Spacecraft | 100 kg, 1 m² cross-section, 400 km circular orbit |

Orbital elements (semi-major axis, eccentricity, specific energy and angular momentum, period) are
recomputed from the state vector at every sample. The simulator reports altitude loss, mean descent
rate and orbital period, keeps the full state history, and then plots five panels with Matplotlib:
altitude decay, orbital velocity, eccentricity evolution, the orbit in the XY plane and a 3D
trajectory. Pygame controls: `Esc` quit, `Space` pause, `+`/`-` zoom, `R` reset zoom.

### `src/j2_drag_odeint.py` — the same physics with `scipy.integrate.odeint`

A compact reference implementation of J2 + drag propagation, useful as a cross-check of the
hand-rolled integrator above.

### `src/astroparser.py` — orbit determination and 3D visualisation

* `skyfield` + `de421.bsp` ephemeris for Earth/Moon/Sun positions;
* `scipy.spatial.transform.Rotation` for framing and attitude transforms;
* `pyvista` for the interactive 3D scene;
* `playwright` + `beautifulsoup4` to pull live latitude/longitude/altitude from the public
  r4uab.ru satellite tracker (DMS parsing, values normalised to decimal degrees).

`astroparser_fixed.py` is a cleaned-up version of the same script after debugging — the original is kept
for reference.

## Layout

```
orbit-dynamics-sim/
├─ src/
│  ├─ dzz_sim/               # LEO satellite simulator
│  │  ├─ config.py           # constants: gravity, atmosphere, orbit, spacecraft
│  │  ├─ satellite.py        # state vector, derivatives, history
│  │  ├─ simulator.py        # Pygame visualisation loop
│  │  ├─ plotter.py          # post-processing plots
│  │  ├─ landing_module.py   # descent-phase helper
│  │  └─ main.py             # entry point
│  ├─ astroparser.py         # TLE / ephemeris positioning + PyVista scene
│  ├─ astroparser_fixed.py   # refactored version
│  └─ j2_drag_odeint.py      # J2 + drag reference propagator
└─ requirements.txt
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Satellite simulator:

```bash
cd src/dzz_sim
python main.py
```

Ephemeris-based positioning (first run downloads `de421.bsp`, ~17 MB):

```bash
cd src
playwright install chromium     # once, for the tracker scraper
python astroparser.py
```

## Notes and limitations

* The atmosphere is a single exponential layer — good enough for order-of-magnitude drag on a 400 km
  orbit, not for precise decay prediction.
* Perturbations from the Sun and Moon, solar radiation pressure and higher-order harmonics are not
  modelled.
* The r4uab.ru tracker scraper depends on the site's DOM (CSS selectors inside an iframe); it is
  expected to break when the site changes and is included as an example of browser automation.

## Stack

Python 3.10+ · NumPy · SciPy · Matplotlib · Pygame · Skyfield · PyVista · Playwright · Beautiful Soup
