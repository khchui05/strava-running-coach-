# Running Coach
### Predicting Race Times and Adapting Training Plans from My Own Strava Data
**Personal project | In progress**

---

## Overview

Generic training plans assume every runner responds the same way. This project uses my own
running history from Strava to answer three questions:

1. **How is my training going?** Track fitness, fatigue, and injury-risk spikes over time.
2. **What can I run right now?** Predict race times from my recent training, and test whether a
   personal model beats the standard formula (Riegel's) that most race calculators use.
3. **What should I run next week?** Generate a training plan that adapts to what I actually
   ran, not what the plan said I'd run.

---

## Roadmap

| Phase | What | Status |
|---|---|---|
| **1. Explore my training** | Clean Strava data, weekly volume, fitness/fatigue, injury-risk (ACWR) flags, Riegel baseline | 🟡 Notebook ready, waiting on data |
| **2. Race-time predictor** | Model race performance from training features; compare against Riegel | ⬜ Planned |
| **3. Adaptive plan generator** | Web app: enter a goal race, get next week's plan, adjusted from logged runs | ⬜ Planned |

### Phase 2 plan
- **Target:** race times, or "race-equivalent" performance estimated from hard efforts if there aren't many races
- **Features:** last 4 to 12 weeks of volume, long run, fitness and form, pace at a given heart rate, elevation, consistency
- **Models:** linear regression with regularization, Random Forest, and gradient boosting, all compared against **Riegel's formula**
- **Validation:** split by time (train on earlier races, test on later ones), since this is time-series data

### Phase 3 plan
- **Stack:** Next.js + PostgreSQL + Prisma, with the Python model served behind an API route
- **Logic:** start from a standard periodized plan (base, build, peak, taper), then adjust each week:
  - missed runs → don't make them up, rebalance the week
  - ACWR above 1.3 → hold volume steady; above 1.5 → cut back
  - predicted race time improving faster than planned → move the goal pace

---

## Key Concepts

**Training load (TRIMP):** each run's load = duration × intensity, where intensity comes from
heart rate. Runs without heart rate fall back to duration only.

**Fitness, fatigue, form:** the Banister impulse-response model.

| Metric | Formula | Meaning |
|---|---|---|
| Fitness | 42-day weighted average load | Long-term training adaptation |
| Fatigue | 7-day weighted average load | Short-term tiredness |
| Form | Fitness − Fatigue | Positive = fresh, negative = tired |

**Acute:chronic workload ratio (ACWR):** last 7 days' load ÷ last 28 days' load. Ratios above
about **1.5** are a commonly cited warning sign for injury risk from ramping up too fast.

**Riegel's formula:** the baseline to beat.

$$T_2 = T_1 \times \left(\frac{D_2}{D_1}\right)^{1.06}$$

---

## Repository Structure

```
├── 01-ExploreTraining.ipynb   # Phase 1: training history, load, injury-risk, Riegel baseline
├── modules/
│   ├── get_data.py            # Downloads my activities from the Strava API
│   └── training.py            # Cleaning, training-load features, Riegel formula
├── data/                      # Personal data, not committed (see data/README.md)
│   ├── 00-raw/
│   ├── 01-interim/
│   └── 02-processed/
├── results/                   # Figures from the notebooks
├── .env.example               # Template for Strava API keys
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Connect to Strava (one time)

1. Go to https://www.strava.com/settings/api and create an app. Any name works; set
   **Authorization Callback Domain** to `localhost`.
2. Copy `.env.example` to `.env` and paste in your **Client ID** and **Client Secret**.
3. Run the authorization step and follow the prompts:

```bash
python modules/get_data.py --auth
```

### 3. Download activities and explore

```bash
python modules/get_data.py
```

```bash
jupyter notebook 01-ExploreTraining.ipynb
```

> 🔒 `.env` (API keys) and everything in `data/` (GPS, heart-rate, and schedule data) are in
> `.gitignore` and never get committed. Only code and summary figures go on GitHub.

---

## Stack

![Python](https://img.shields.io/badge/Python-3-blue)
![Pandas](https://img.shields.io/badge/Pandas-data-lightblue)
![scikit--learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![Strava API](https://img.shields.io/badge/Strava-API-FC4C02)
![Next.js](https://img.shields.io/badge/Next.js-planned-black)

---

## Author

**Katherine Chui**, UC San Diego

---

## References

1. Riegel, P. S. (1981). Athletic records and human endurance. *American Scientist*, 69(3), 285–290.
2. Banister, E. W., Calvert, T. W., Savage, M. V., & Bach, T. (1975). A systems model of training for athletic performance. *Australian Journal of Sports Medicine*, 7, 57–61.
3. Gabbett, T. J. (2016). The training–injury prevention paradox: should athletes be training smarter and harder? *British Journal of Sports Medicine*, 50(5), 273–280.
4. Strava API documentation. https://developers.strava.com/docs/reference/
