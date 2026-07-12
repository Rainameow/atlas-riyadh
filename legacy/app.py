import pandas as pd
import pydeck as pdk
import streamlit as st

from atlas.config import DEFAULT_POPULATION, RIYADH_CENTER
from atlas.data import EVENT_PRESETS, WEATHER_PRESETS
from atlas.simulation import CitySimulation


st.set_page_config(
    page_title="Atlas Riyadh",
    page_icon="🌐",
    layout="wide",
)

st.title("Atlas Riyadh")
st.caption("A lightweight digital twin showing how weather and city events change movement across Riyadh.")

with st.sidebar:
    st.header("Simulation controls")
    population = st.slider("Population", 100, 2_000, DEFAULT_POPULATION, 100)
    weather = st.selectbox("Weather", list(WEATHER_PRESETS))
    event = st.selectbox("City event", list(EVENT_PRESETS))
    minutes = st.select_slider("Minutes per step", options=[15, 30, 60, 120], value=30)

    if "simulation" not in st.session_state or st.session_state.get("population") != population:
        st.session_state.simulation = CitySimulation(population=population)
        st.session_state.population = population

    simulation: CitySimulation = st.session_state.simulation
    simulation.set_conditions(weather, event)

    step_clicked = st.button("Advance simulation", use_container_width=True)
    if step_clicked:
        simulation.step(minutes=minutes)

    if st.button("Reset simulation", use_container_width=True):
        st.session_state.simulation = CitySimulation(population=population)
        simulation = st.session_state.simulation

    st.divider()
    st.subheader("Current conditions")
    st.write(WEATHER_PRESETS[weather]["description"])
    st.write(EVENT_PRESETS[event]["description"])

metrics = simulation.metrics()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Simulated time", f"{metrics['hour']:04.1f}:00")
col2.metric("Citizens moving", metrics["traveling"])
col3.metric("Leisure trips", metrics["leisure_trips"])
col4.metric("Population", metrics["population"])

citizens = simulation.citizens_frame()
districts = simulation.district_activity_frame()

citizen_layer = pdk.Layer(
    "ScatterplotLayer",
    data=citizens,
    get_position="[lon, lat]",
    get_radius=95,
    pickable=True,
    opacity=0.55,
)

district_layer = pdk.Layer(
    "ScatterplotLayer",
    data=districts,
    get_position="[lon, lat]",
    get_radius="activity * 8 + 180",
    pickable=True,
    opacity=0.35,
)

labels_layer = pdk.Layer(
    "TextLayer",
    data=districts,
    get_position="[lon, lat]",
    get_text="district",
    get_size=14,
    get_alignment_baseline="'bottom'",
    pickable=False,
)

view_state = pdk.ViewState(
    latitude=RIYADH_CENTER["lat"],
    longitude=RIYADH_CENTER["lon"],
    zoom=9.7,
    pitch=35,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[district_layer, citizen_layer, labels_layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{district}</b><br/>Activity: {activity}<br/>Destination: {destination}",
            "style": {"backgroundColor": "black", "color": "white"},
        },
    ),
    use_container_width=True,
)

left, right = st.columns([1.2, 1])

with left:
    st.subheader("District activity")
    chart_data = districts.set_index("district")[["activity"]]
    st.bar_chart(chart_data)

with right:
    st.subheader("Top destinations")
    st.dataframe(
        districts[["district", "type", "activity"]].head(8),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("What Atlas is testing")
st.write(
    "Change the weather or trigger a city event, then advance the simulation. "
    "Citizens update their destinations and movement speed based on those conditions."
)
