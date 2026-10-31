# -*- coding: utf-8 -*-
import os
import io
from datetime import date

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk

# ---------------- Configuration ----------------
st.set_page_config(
    page_title="COPAG | Pilotage logistique",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Démo locale uniquement : remplacez ces valeurs par des secrets/env vars
# avant tout déploiement public.
def get_credentials():
    try:
        username = st.secrets.get("username", os.getenv("COPAG_USERNAME", "hajar"))
        password = st.secrets.get("password", os.getenv("COPAG_PASSWORD", "ha2707"))
    except Exception:
        username = os.getenv("COPAG_USERNAME", "hajar")
        password = os.getenv("COPAG_PASSWORD", "ha2707")
    return str(username), str(password)

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({"figure.figsize": (9, 4.2), "axes.titlesize": 12, "axes.labelsize": 10})

# ---------------- Style ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background: #f4f7fb;}
[data-testid="stSidebar"] {background: #102b3f;}
[data-testid="stSidebar"] * {color: #f4f8fb;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:#183247;}
h1,h2,h3 {font-family:'Manrope',sans-serif;color:#142f43;}
.hero {background:linear-gradient(115deg,#102f45,#176b63);padding:26px 30px;border-radius:18px;color:white;margin-bottom:18px;}
.hero h1 {color:white;margin:0;font-size:30px;}
.hero p {color:#d9ece9;margin:6px 0 0 0;}
.kpi {background:white;border:1px solid #e5ebf1;border-radius:15px;padding:17px 18px;min-height:112px;box-shadow:0 3px 14px rgba(19,48,68,.045);}
.kpi-label {font-size:12px;color:#718096;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.kpi-value {font-family:'Manrope';font-size:25px;color:#173b50;font-weight:800;margin-top:7px;}
.kpi-note {font-size:11px;color:#81909c;margin-top:2px;}
.section {font-family:'Manrope';font-weight:800;color:#16364a;font-size:18px;margin:18px 0 8px;}
.panel {background:white;border:1px solid #e6edf2;border-radius:15px;padding:14px 16px;}
.small-muted {color:#6b7d8b;font-size:12px;}
div[data-testid="stMetric"] {background:white;padding:14px;border:1px solid #e5ebf1;border-radius:14px;}
.stButton>button {border-radius:10px;background:#167568;color:white;border:0;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ---------------- Authentification ----------------
def login_screen():
    st.markdown("<div class='hero'><h1>🚚 COPAG Logistics Intelligence</h1><p>Plateforme de pilotage des opérations de transport au Maroc</p></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.05, 1])
    with center:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Connexion à votre espace")
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", placeholder="Votre identifiant")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted:
            expected_user, expected_password = get_credentials()
            if username == expected_user and password == expected_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
        st.markdown("<p class='small-muted'>Accès réservé aux utilisateurs autorisés.</p></div>", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    login_screen()
    st.stop()

# ---------------- Données ----------------
@st.cache_data
def load_data(csv_bytes):
    data = pd.read_csv(io.BytesIO(csv_bytes))
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    numeric = [
        "distance_km", "planned_duration_min", "actual_duration_min", "delay_min",
        "on_time", "temperature_breach", "capacity_utilization", "fuel_liters",
        "co2_kg", "cost_mad", "quantity_tons", "lat", "lon", "o_lat", "o_lon",
        "d_lat", "d_lon"
    ]
    for col in numeric:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data["lane"] = data["origin_hub"].astype(str) + " → " + data["destination_city"].astype(str)
    # La vitesse n'est pas une colonne source : elle est estimée à partir de la distance et du temps réel.
    data["speed_kmh"] = np.where(
        data["actual_duration_min"] > 0,
        data["distance_km"] / (data["actual_duration_min"] / 60),
        np.nan
    )
    data["cost_per_km"] = np.where(data["distance_km"] > 0, data["cost_mad"] / data["distance_km"], np.nan)
    return data

# ---------------- Import du dataset ----------------
st.markdown("### Importer les données")
uploaded_file = st.file_uploader(
    "Choisissez votre fichier CSV COPAG",
    type=["csv"],
    help="Le fichier doit contenir les colonnes décrites dans le README."
)
if uploaded_file is None:
    st.info("Pour commencer, importez votre fichier copag_logistics.csv. Aucun dataset n'est inclus dans ce projet.")
    st.stop()

try:
    df = load_data(uploaded_file.getvalue())
except Exception as exc:
    st.error(f"Impossible de lire le fichier CSV : {exc}")
    st.stop()

required_columns = [
    "date", "origin_hub", "destination_city", "destination_region",
    "distance_km", "planned_duration_min", "actual_duration_min",
    "delay_min", "on_time", "mode", "product_category", "fuel_liters",
    "co2_kg", "cost_mad", "lat", "lon", "o_lat", "o_lon", "d_lat", "d_lon"
]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error("Colonnes manquantes dans le CSV : " + ", ".join(missing_columns))
    st.stop()

# ---------------- Sidebar / filtres ----------------
with st.sidebar:
    st.markdown("## COPAG")
    st.caption("Centre de contrôle logistique")
    if st.button("↪ Déconnexion", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")
    st.markdown("### Filtres")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input("Période", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    regions = st.multiselect("Région de destination", sorted(df["destination_region"].dropna().unique()))
    modes = st.multiselect("Mode de transport", sorted(df["mode"].dropna().unique()))
    products = st.multiselect("Catégorie de produit", sorted(df["product_category"].dropna().unique()))
    hubs = st.multiselect("Hub de départ", sorted(df["origin_hub"].dropna().unique()))
    cities = st.multiselect("Ville de destination", sorted(df["destination_city"].dropna().unique()))
    st.markdown("---")
    st.caption("Les filtres s'appliquent à tous les indicateurs et graphiques.")

fdf = df.copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    fdf = fdf[fdf["date"].dt.date.between(date_range[0], date_range[1])]
elif isinstance(date_range, date):
    fdf = fdf[fdf["date"].dt.date == date_range]
if regions: fdf = fdf[fdf["destination_region"].isin(regions)]
if modes: fdf = fdf[fdf["mode"].isin(modes)]
if products: fdf = fdf[fdf["product_category"].isin(products)]
if hubs: fdf = fdf[fdf["origin_hub"].isin(hubs)]
if cities: fdf = fdf[fdf["destination_city"].isin(cities)]

# ---------------- En-tête ----------------
st.markdown("""
<div class="hero">
  <h1>Tableau de bord logistique</h1>
  <p>Suivi des livraisons • performance • coûts • carburant • émissions CO₂ • flotte nationale</p>
</div>
""", unsafe_allow_html=True)
st.caption(f"Vue filtrée : {len(fdf):,} expédition(s) sur {len(df):,} • Données du {df.date.min():%d/%m/%Y} au {df.date.max():%d/%m/%Y}")

if fdf.empty:
    st.warning("Aucune expédition ne correspond aux filtres sélectionnés. Modifiez les filtres dans la barre latérale.")
    st.stop()

# ---------------- KPI ----------------
def metric_card(label, value, note):
    st.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div><div class='kpi-note'>{note}</div></div>", unsafe_allow_html=True)

n = len(fdf)
on_time = fdf["on_time"].mean() * 100
avg_cost = fdf["cost_mad"].mean()
avg_fuel = fdf["fuel_liters"].mean()
avg_co2 = fdf["co2_kg"].mean()
avg_distance = fdf["distance_km"].mean()
avg_speed = fdf["speed_kmh"].mean()
k = st.columns(6)
with k[0]: metric_card("Expéditions", f"{n:,.0f}", "Volume sélectionné")
with k[1]: metric_card("À l'heure", f"{on_time:.1f} %", "Taux de ponctualité")
with k[2]: metric_card("Coût moyen", f"{avg_cost:,.0f} MAD", "Par expédition")
with k[3]: metric_card("Carburant moyen", f"{avg_fuel:,.1f} L", "Litres par trajet")
with k[4]: metric_card("CO₂ moyen", f"{avg_co2:,.1f} kg", "Kg par expédition")
with k[5]: metric_card("Vitesse moyenne", f"{avg_speed:.1f} km/h", "Estimée sur temps réel")

st.markdown("<div class='section'>Performance & itinéraires</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    daily = fdf.groupby(fdf["date"].dt.date)["on_time"].mean().mul(100).reset_index(name="taux")
    fig, ax = plt.subplots()
    ax.plot(daily.iloc[:,0], daily["taux"], marker="o", linewidth=2)
    ax.set(title="Ponctualité quotidienne", xlabel="Date", ylabel="Livraisons à l'heure (%)")
    ax.tick_params(axis="x", rotation=35)
    ax.set_ylim(0, 105)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)
with c2:
    top = fdf["lane"].value_counts().head(10).rename_axis("Route").reset_index(name="Expéditions")
    fig, ax = plt.subplots(figsize=(9, 4.2))
    sns.barplot(data=top, x="Expéditions", y="Route", ax=ax)
    ax.set(title="Top 10 des routes par volume", xlabel="Nombre d'expéditions", ylabel="")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section'>Retards & corrélations</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    fig, ax = plt.subplots()
    sns.boxplot(data=fdf, x="delay_min", y="product_category", ax=ax)
    ax.set(title="Distribution des retards par produit", xlabel="Retard (minutes)", ylabel="Catégorie")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)
with c2:
    numeric_cols = ["distance_km","planned_duration_min","actual_duration_min","delay_min","on_time","temperature_breach","capacity_utilization","fuel_liters","co2_kg","cost_mad","quantity_tons","speed_kmh"]
    corr = fdf[numeric_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(corr, cmap="vlag", center=0, annot=True, fmt=".1f", ax=ax, annot_kws={"size":7})
    ax.set_title("Matrice de corrélation")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section'>Coûts & répartition</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    cost_region = fdf.groupby("destination_region", as_index=False)["cost_per_km"].mean().sort_values("cost_per_km", ascending=False)
    fig, ax = plt.subplots()
    sns.barplot(data=cost_region, x="destination_region", y="cost_per_km", ax=ax)
    ax.set(title="Coût moyen par kilomètre et par région", xlabel="Région", ylabel="MAD / km")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)
with c2:
    product_counts = fdf["product_category"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(product_counts.values, labels=product_counts.index, autopct="%1.1f%%", startangle=90, wedgeprops={"width":0.48})
    ax.set_title("Part des expéditions par produit")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section'>Analyse carburant, distance & vitesse</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    fig, ax = plt.subplots()
    sns.scatterplot(data=fdf, x="distance_km", y="fuel_liters", hue="mode", alpha=.7, ax=ax)
    ax.set(title="Distance et consommation de carburant", xlabel="Distance (km)", ylabel="Carburant (L)")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)
with c2:
    fig, ax = plt.subplots()
    sns.scatterplot(data=fdf, x="distance_km", y="speed_kmh", hue="mode", alpha=.7, ax=ax)
    ax.set(title="Distance et vitesse moyenne estimée", xlabel="Distance (km)", ylabel="Vitesse (km/h)")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section'>Cartographie de la flotte et des flux</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Positions de la flotte (coordonnées du dataset)**")
    fleet = fdf[["lat","lon"]].dropna().rename(columns={"lat":"latitude","lon":"longitude"})
    if not fleet.empty:
        st.map(fleet, use_container_width=True)
    else:
        st.info("Aucune coordonnée de flotte disponible pour cette sélection.")
with c2:
    st.markdown("**Flux entre les hubs et les villes**")
    flows = fdf.groupby(["origin_hub","destination_city","o_lat","o_lon","d_lat","d_lon"], as_index=False).size().rename(columns={"size":"volume"})
    flows = flows.dropna(subset=["o_lat","o_lon","d_lat","d_lon"])
    if not flows.empty:
        layer = pdk.Layer(
            "ArcLayer", data=flows, get_source_position=["o_lon","o_lat"],
            get_target_position=["d_lon","d_lat"], get_width="2 + volume",
            get_tilt=15, get_source_color=[22,119,105,150],
            get_target_color=[235,145,55,170], pickable=True, auto_highlight=True
        )
        view = pdk.ViewState(latitude=float(fdf["d_lat"].mean()), longitude=float(fdf["d_lon"].mean()), zoom=4.1, pitch=35)
        deck = pdk.Deck(layers=[layer], initial_view_state=view, tooltip={"text":"{origin_hub} → {destination_city}\\nExpéditions : {volume}"})
        st.pydeck_chart(deck, use_container_width=True)
    else:
        st.info("Aucun flux géographique disponible.")

# ---------------- Analyse et données ----------------
st.markdown("<div class='section'>Points de vigilance</div>", unsafe_allow_html=True)
a, b, c = st.columns(3)
late_rate = 100 - on_time
breach_rate = fdf["temperature_breach"].mean() * 100
with a: st.metric("Livraisons en retard", f"{late_rate:.1f} %")
with b: st.metric("Rupture chaîne du froid", f"{breach_rate:.1f} %")
with c: st.metric("Retard moyen", f"{fdf['delay_min'].mean():.1f} min")
worst_routes = fdf.groupby("lane").agg(expeditions=("shipment_id","count"), retard_moyen=("delay_min","mean"), cout_moyen=("cost_mad","mean")).sort_values(["retard_moyen","expeditions"], ascending=False).head(5)
st.markdown("**Routes à surveiller (selon le retard moyen)**")
st.dataframe(worst_routes.style.format({"retard_moyen":"{:.1f} min","cout_moyen":"{:,.0f} MAD"}), use_container_width=True)

with st.expander("Consulter les expéditions filtrées"):
    st.dataframe(fdf.drop(columns=["lane"], errors="ignore"), use_container_width=True, hide_index=True)
    csv = fdf.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Télécharger la sélection (CSV)", csv, "copag_expeditions_filtrees.csv", "text/csv")

st.markdown("---")
st.markdown("<p class='small-muted'>COPAG • Dashboard pédagogique de suivi logistique • Les vitesses sont calculées comme distance / durée réelle. Les positions de flotte correspondent aux coordonnées fournies dans le fichier et ne constituent pas un suivi GPS en temps réel.</p>", unsafe_allow_html=True)
