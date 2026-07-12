DISTRICTS = [
    {"name": "Olaya", "lat": 24.7117, "lon": 46.6744, "type": "business"},
    {"name": "KAFD", "lat": 24.7674, "lon": 46.6432, "type": "business"},
    {"name": "Diriyah", "lat": 24.7345, "lon": 46.5757, "type": "leisure"},
    {"name": "King Abdullah Park", "lat": 24.6628, "lon": 46.7374, "type": "leisure"},
    {"name": "Al Malqa", "lat": 24.8030, "lon": 46.6252, "type": "residential"},
    {"name": "Al Yasmin", "lat": 24.8270, "lon": 46.6365, "type": "residential"},
    {"name": "Al Nakheel", "lat": 24.7486, "lon": 46.6527, "type": "residential"},
    {"name": "Riyadh Front", "lat": 24.8411, "lon": 46.7331, "type": "leisure"},
    {"name": "King Saud University", "lat": 24.7251, "lon": 46.6185, "type": "education"},
    {"name": "King Khalid Airport", "lat": 24.9576, "lon": 46.6988, "type": "transport"},
]

WEATHER_PRESETS = {
    "Clear": {
        "speed_multiplier": 1.0,
        "leisure_multiplier": 1.0,
        "description": "Normal city activity.",
    },
    "Heatwave": {
        "speed_multiplier": 0.82,
        "leisure_multiplier": 0.55,
        "description": "Outdoor movement falls and trips take longer.",
    },
    "Sandstorm": {
        "speed_multiplier": 0.55,
        "leisure_multiplier": 0.30,
        "description": "Visibility drops and nonessential travel decreases.",
    },
    "Rain": {
        "speed_multiplier": 0.72,
        "leisure_multiplier": 0.65,
        "description": "Road speeds drop and indoor destinations become more popular.",
    },
}

EVENT_PRESETS = {
    "None": {
        "target": None,
        "pull": 0.0,
        "congestion": 1.0,
        "description": "No major city event.",
    },
    "Riyadh Season Concert": {
        "target": "Riyadh Front",
        "pull": 0.28,
        "congestion": 0.78,
        "description": "Large evening crowds travel toward Riyadh Front.",
    },
    "Football Match": {
        "target": "King Abdullah Park",
        "pull": 0.22,
        "congestion": 0.82,
        "description": "A major match creates a temporary activity spike.",
    },
    "KAFD Road Closure": {
        "target": "KAFD",
        "pull": -0.15,
        "congestion": 0.62,
        "description": "Traffic avoids KAFD and nearby routes slow down.",
    },
}
