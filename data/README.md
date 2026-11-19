# Data

All data comes from **your own Strava account** through the Strava API. Nothing in here is committed. It contains personal location, heart-rate, and schedule data, so it stays on your machine.

| File | Made by | Contents |
|---|---|---|
| `00-raw/strava_activities.json` | `python modules/get_data.py` | Every activity, exactly as the Strava API returns it |
| `02-processed/runs.csv` | `01-ExploreTraining.ipynb` | One row per run, cleaned, in readable units |

## Columns in `runs.csv`

| Column | Meaning |
|---|---|
| `date` | Local start time |
| `type` | Run, TrailRun, or VirtualRun (treadmill) |
| `distance_km`, `moving_min`, `elapsed_min` | Distance and time |
| `pace_min_per_km` | Moving time ÷ distance |
| `elev_gain_m` | Total elevation gain |
| `avg_hr`, `max_hr` | Heart rate (missing if no HR monitor) |
| `avg_cadence_spm` | Steps per minute |
| `workout_type` | easy / race / long / workout, from the Run type you set in Strava |

## Cleaning rules

- Keep only runs (no rides, hikes, etc.)
- Drop runs under 0.5 km or with impossible paces (faster than 2:30/km or slower than 15:00/km), which are usually GPS glitches or forgotten-to-stop watches
