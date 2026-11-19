"""Cleaning, training-load features, and race-time baselines.

Used by the notebooks:
    from modules.training import load_runs, daily_load, training_load, riegel
"""
import json

import numpy as np
import pandas as pd

RUN_TYPES = {"Run", "TrailRun", "VirtualRun"}
RACE_DISTANCES_M = {"1 mile": 1609.34, "5K": 5000, "10K": 10000, "Half marathon": 21097.5, "Marathon": 42195}


# ---- cleaning -------------------------------------------------------------------

def load_runs(path="data/00-raw/strava_activities.json"):
    """Strava activities JSON -> one row per run, with units a runner can read."""
    acts = pd.DataFrame(json.load(open(path)))
    type_col = "sport_type" if "sport_type" in acts else "type"
    runs = acts[acts[type_col].isin(RUN_TYPES)].copy()

    out = pd.DataFrame({
        "id": runs["id"],
        "date": pd.to_datetime(runs["start_date_local"]).dt.tz_localize(None),
        "name": runs["name"],
        "type": runs[type_col],
        "distance_km": runs["distance"] / 1000,
        "moving_min": runs["moving_time"] / 60,
        "elapsed_min": runs["elapsed_time"] / 60,
        "elev_gain_m": runs.get("total_elevation_gain"),
        "avg_hr": runs.get("average_heartrate"),
        "max_hr": runs.get("max_heartrate"),
        "avg_cadence_spm": runs.get("average_cadence", pd.Series(np.nan, index=runs.index)) * 2,  # Strava reports one foot
        # Strava workout_type for runs: 0 default, 1 race, 2 long run, 3 workout
        "workout_type": runs.get("workout_type").map({0: "easy", 1: "race", 2: "long", 3: "workout"}),
    })
    out["pace_min_per_km"] = out["moving_min"] / out["distance_km"]

    # Drop obvious junk: GPS glitches, accidental starts
    out = out[(out["distance_km"] >= 0.5) & out["pace_min_per_km"].between(2.5, 15)]
    return out.sort_values("date").reset_index(drop=True)


# ---- training load ----------------------------------------------------------------

def run_load(runs, max_hr=None, rest_hr=60):
    """Training load per run.

    Uses heart-rate TRIMP (Banister) when heart rate is available:
        load = minutes × HRr × 0.64 × e^(1.92 × HRr),  HRr = (avg HR − rest) / (max HR − rest)
    and falls back to minutes × 1 for runs without heart rate.
    """
    max_hr = max_hr or runs["max_hr"].quantile(0.99)
    hrr = ((runs["avg_hr"] - rest_hr) / (max_hr - rest_hr)).clip(0, 1)
    trimp = runs["moving_min"] * hrr * 0.64 * np.exp(1.92 * hrr)
    return trimp.fillna(runs["moving_min"])


def daily_load(runs, **kwargs):
    """Total load per calendar day, including rest days as 0."""
    s = pd.Series(run_load(runs, **kwargs).values, index=runs["date"].dt.normalize())
    s = s.groupby(level=0).sum()
    return s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"), fill_value=0)


def training_load(daily):
    """Fitness, fatigue, form, and acute:chronic workload ratio from daily load.

    - fitness (CTL): 42-day exponentially weighted average load
    - fatigue (ATL): 7-day exponentially weighted average load
    - form (TSB):    fitness − fatigue (positive = fresh, negative = tired)
    - ACWR:          7-day average ÷ 28-day average. Above about 1.5 is a commonly cited injury-risk zone.
    """
    df = pd.DataFrame({"load": daily})
    df["fitness"] = daily.ewm(span=42, adjust=False).mean()
    df["fatigue"] = daily.ewm(span=7, adjust=False).mean()
    df["form"] = df["fitness"] - df["fatigue"]
    df["acwr"] = daily.rolling(7).mean() / daily.rolling(28).mean()
    df["risk_flag"] = df["acwr"] > 1.5
    return df


def weekly_summary(runs):
    w = runs.set_index("date").resample("W-MON", label="left", closed="left")
    return pd.DataFrame({
        "runs": w["id"].count(),
        "km": w["distance_km"].sum(),
        "hours": w["moving_min"].sum() / 60,
        "long_run_km": w["distance_km"].max(),
        "elev_gain_m": w["elev_gain_m"].sum(),
    })


# ---- race-time baselines ---------------------------------------------------------

def riegel(known_time_min, known_dist_m, target_dist_m, exponent=1.06):
    """Riegel's formula: T2 = T1 × (D2 / D1) ^ 1.06. The baseline the model has to beat."""
    return known_time_min * (target_dist_m / known_dist_m) ** exponent


def fmt_time(minutes):
    """72.5 -> '1:12:30'"""
    s = int(round(minutes * 60))
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
