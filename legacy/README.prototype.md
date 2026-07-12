# Atlas Riyadh

Atlas is a lightweight digital twin prototype for Riyadh. It simulates citizens moving between districts as weather and city events change behavior.

## Features

- Synthetic Riyadh districts with geographic coordinates
- Citizens with home, work, and leisure destinations
- Time-based movement patterns
- Weather effects such as heatwaves, rain, and sandstorms
- City events such as concerts, football matches, and road closures
- Live Streamlit dashboard with maps, KPIs, and district activity
- Unit tests for simulation behavior

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
pytest
```

## Project structure

```text
atlas-riyadh/
├── app.py
├── atlas/
│   ├── __init__.py
│   ├── config.py
│   ├── data.py
│   ├── models.py
│   └── simulation.py
├── tests/
│   └── test_simulation.py
└── requirements.txt
```

## Why this project exists

Most city dashboards only show what has already happened. Atlas explores a different question: what might happen next if weather, public events, infrastructure, or population behavior changes?
