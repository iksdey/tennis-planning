import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import planning


st.set_page_config(
    page_title="Planning tennis",
    layout="wide",
)


TOURNOIS_PATH = Path("tournois.json")
TOURNAMENT_COLUMNS = [
    "club",
    "type",
    "debut",
    "fin",
    "entree_reelle",
    "classement_min",
    "classement_max",
]

CLASSEMENT_JOUEUR = "15/5"

PONDERATION_JOURS = {
    "lundi": 1,
    "mardi": 1,
    "mercredi": 1,
    "jeudi": 1,
    "vendredi": 1,
    "samedi": 1.5,
    "dimanche": 1.5,
    "ferie": 1.5,
}

CLASSEMENTS = [
    "NC", "40", "30/5", "30/4", "30/3", "30/2", "30/1", "30",
    "15/5", "15/4", "15/3", "15/2", "15/1", "15",
    "5/6", "4/6", "3/6", "2/6", "1/6", "0",
    "-2/6", "-4/6", "-15"
]

TOURNAMENT_COLOR = "grey"
TMC_COLOR = "purple"
PARTICIPATION_COLOR = "royalblue"

DATE_FORMAT = "%d/%m"

TEXT_COLOR = "white"
ANNOTATION_FONT_SIZE = 15
AXIS_FONT_SIZE = 18
BAR_WIDTH = 0.95
MIN_CHART_HEIGHT = 450
CHART_ROW_HEIGHT = 125

HOVER_DATA = {
    "debut": False,
    "fin": False,
    "club": False,
    "entree_reelle": True,
}


def build_chart(tournois):
    df = pd.DataFrame(tournois)

    df = planning.preparer_tournois(
        df,
        CLASSEMENT_JOUEUR,
        PONDERATION_JOURS,
        TOURNAMENT_COLOR,
        TMC_COLOR,
    )
    df["entree_reelle_hover"] = df["entree_reelle"].apply(
        lambda date: "" if pd.isna(date) else pd.to_datetime(date).strftime("%d/%m/%Y")
    )

    df_classiques = planning.tournois_classiques(df)

    fig = px.timeline(
        df,
        x_start="debut",
        x_end="fin",
        y="club",
        hover_data=HOVER_DATA
    )

    fig.update_traces(
        marker_color=df["couleur_barre"].tolist(),
        width=BAR_WIDTH,
        customdata=df[["entree_reelle_hover"]].to_numpy(),
        hovertemplate=[
            ""
            if planning.est_tmc(row["type"]) or not row["entree_reelle_hover"]
            else "Entrée réelle : %{customdata[0]}<extra></extra>"
            for _, row in df.iterrows()
        ],
    )

    fig_participation = px.timeline(
        df_classiques,
        x_start="debut_participation",
        x_end="fin",
        y="club",
    )
    fig_participation.update_traces(
        marker_color=PARTICIPATION_COLOR,
        width=BAR_WIDTH,
        hoverinfo="skip",
        hovertemplate=None,
    )

    fig.add_traces(fig_participation.data)

    for _, row in df.iterrows():
        debut_label = pd.to_datetime(row["debut"]).strftime(DATE_FORMAT)
        fin_label = pd.to_datetime(row["fin"]).strftime(DATE_FORMAT)
        est_tmc = planning.est_tmc(row["type"])
        tmc_label_x = row["debut"] + (row["fin"] - row["debut"]) / 2
        classement_min = row.get("classement_min")
        classement_max = row.get("classement_max")

        if planning.est_classique(row["type"]) and pd.notna(row["entree_reelle"]):
            fig.add_shape(
                type="line",
                x0=row["entree_reelle"],
                x1=row["entree_reelle"],
                y0=row["club"],
                y1=row["club"],
                y0shift=-BAR_WIDTH / 2,
                y1shift=BAR_WIDTH / 2,
                xref="x",
                yref="y",
                line={"color": "red", "width": 3},
            )

        fig.add_annotation(
            x=tmc_label_x if est_tmc else row["debut"],
            y=row["club"],
            text=f"{debut_label} -> {fin_label}" if est_tmc else debut_label,
            showarrow=False,
            xanchor="center" if est_tmc else "left",
            yanchor="middle" if est_tmc else None,
            yshift=-16 if est_tmc else 0,
            align="center" if est_tmc else None,
            font={"color": TEXT_COLOR, "size": ANNOTATION_FONT_SIZE},
            bgcolor="black" if est_tmc else None,
        )

        if not est_tmc:
            fig.add_annotation(
                x=row["fin"],
                y=row["club"],
                text=fin_label,
                showarrow=False,
                xanchor="right",
                font={"color": TEXT_COLOR, "size": ANNOTATION_FONT_SIZE},
            )

        if planning.est_classique(row["type"]) and pd.notna(row["debut_participation"]):
            fig.add_annotation(
                x=row["debut_participation"],
                y=row["club"],
                text=pd.to_datetime(row["debut_participation"]).strftime(DATE_FORMAT),
                showarrow=False,
                xanchor="left",
                font={"color": TEXT_COLOR, "size": ANNOTATION_FONT_SIZE},
            )

        if pd.notna(classement_min) and pd.notna(classement_max):
            fig.add_annotation(
                x=row["debut"] + (row["fin"] - row["debut"]) / 2,
                y=row["club"],
                text=f"{classement_min} -> {classement_max}",
                showarrow=False,
                xanchor="center",
                yanchor="middle" if est_tmc else "top",
                yshift=16 if est_tmc else 42,
                font={"color": TEXT_COLOR, "size": ANNOTATION_FONT_SIZE},
                bgcolor="black",
            )

    fig.update_xaxes(tickfont={"size": AXIS_FONT_SIZE})
    fig.update_yaxes(
        autorange="reversed",
        tickfont={"size": AXIS_FONT_SIZE},
    )
    fig.update_layout(
        font={"size": AXIS_FONT_SIZE},
        hoverlabel={"font_size": AXIS_FONT_SIZE},
        height=max(MIN_CHART_HEIGHT, CHART_ROW_HEIGHT * len(df)),
    )

    return fig, df


def load_tournois():
    with TOURNOIS_PATH.open(encoding="utf-8") as fichier_tournois:
        tournois = json.load(fichier_tournois)

    return [normalize_tournoi(tournoi) for tournoi in tournois]


def normalize_tournoi(tournoi):
    normalized = {column: tournoi.get(column, "") for column in TOURNAMENT_COLUMNS}
    normalized["club"] = str(normalized["club"]).strip()
    normalized["type"] = normalized["type"] or "classique"
    normalized["classement_min"] = normalized["classement_min"] or "NC"
    normalized["classement_max"] = normalized["classement_max"] or "15/1"

    return normalized


def tournois_to_editor_df(tournois):
    if not tournois:
        return pd.DataFrame({
            "club": pd.Series(dtype="string"),
            "type": pd.Series(dtype="string"),
            "debut": pd.Series(dtype="datetime64[ns]"),
            "fin": pd.Series(dtype="datetime64[ns]"),
            "entree_reelle": pd.Series(dtype="datetime64[ns]"),
            "classement_min": pd.Series(dtype="string"),
            "classement_max": pd.Series(dtype="string"),
        })

    df = pd.DataFrame(tournois, columns=TOURNAMENT_COLUMNS)

    for column in ("debut", "fin", "entree_reelle"):
        df[column] = df[column].apply(planning.parse_date_fr)

    return df


def format_date_fr(date_value):
    date = planning.parse_date_fr(date_value)

    if pd.isna(date):
        return ""

    return date.strftime(planning.DATE_FORMAT_FR)


def editor_df_to_tournois(df):
    tournois = []

    for _, row in df.iterrows():
        tournoi = {
            "club": "" if pd.isna(row["club"]) else str(row["club"]).strip(),
            "type": "" if pd.isna(row["type"]) else str(row["type"]).strip(),
            "debut": format_date_fr(row["debut"]),
            "fin": format_date_fr(row["fin"]),
            "entree_reelle": format_date_fr(row["entree_reelle"]),
            "classement_min": "" if pd.isna(row["classement_min"]) else str(row["classement_min"]).strip(),
            "classement_max": "" if pd.isna(row["classement_max"]) else str(row["classement_max"]).strip(),
        }

        if any(tournoi.values()):
            tournois.append(normalize_tournoi(tournoi))

    return tournois


def validate_tournois(tournois):
    errors = []

    for index, tournoi in enumerate(tournois, start=1):
        prefix = f"Ligne {index}"
        debut = planning.parse_date_fr(tournoi["debut"])
        fin = planning.parse_date_fr(tournoi["fin"])

        if not tournoi["club"]:
            errors.append(f"{prefix} : le club est obligatoire.")

        if tournoi["type"] not in ("classique", "TMC"):
            errors.append(f"{prefix} : le type doit être classique ou TMC.")

        if pd.isna(debut):
            errors.append(f"{prefix} : la date de début est obligatoire.")

        if pd.isna(fin):
            errors.append(f"{prefix} : la date de fin est obligatoire.")

        if pd.notna(debut) and pd.notna(fin) and fin < debut:
            errors.append(f"{prefix} : la date de fin doit être après la date de début.")

        if tournoi["classement_min"] not in CLASSEMENTS:
            errors.append(f"{prefix} : le classement min est invalide.")

        if tournoi["classement_max"] not in CLASSEMENTS:
            errors.append(f"{prefix} : le classement max est invalide.")

        if (
            tournoi["classement_min"] in CLASSEMENTS
            and tournoi["classement_max"] in CLASSEMENTS
            and CLASSEMENTS.index(tournoi["classement_min"]) > CLASSEMENTS.index(tournoi["classement_max"])
        ):
            errors.append(f"{prefix} : le classement min doit être inférieur ou égal au classement max.")

    return errors


def save_tournois(tournois):
    with TOURNOIS_PATH.open("w", encoding="utf-8") as fichier_tournois:
        json.dump(tournois, fichier_tournois, ensure_ascii=False, indent=2)
        fichier_tournois.write("\n")


st.title("Road to -15")

if "tournois" not in st.session_state:
    st.session_state.tournois = load_tournois()

if "tournois_editor_version" not in st.session_state:
    st.session_state.tournois_editor_version = 0

chart_container = st.container()

st.subheader("Tournois")

edited_df = st.data_editor(
    tournois_to_editor_df(st.session_state.tournois),
    key=f"tournois_editor_{st.session_state.tournois_editor_version}",
    num_rows="dynamic",
    hide_index=True,
    column_order=TOURNAMENT_COLUMNS,
    column_config={
        "club": st.column_config.TextColumn("Club", required=True),
        "type": st.column_config.SelectboxColumn(
            "Type",
            options=["classique", "TMC"],
            required=True,
        ),
        "debut": st.column_config.DateColumn(
            "Début",
            format="DD/MM/YYYY",
            required=True,
        ),
        "fin": st.column_config.DateColumn(
            "Fin",
            format="DD/MM/YYYY",
            required=True,
        ),
        "entree_reelle": st.column_config.DateColumn(
            "Entrée réelle",
            format="DD/MM/YYYY",
        ),
        "classement_min": st.column_config.SelectboxColumn(
            "Classement min",
            options=CLASSEMENTS,
            required=True,
        ),
        "classement_max": st.column_config.SelectboxColumn(
            "Classement max",
            options=CLASSEMENTS,
            required=True,
        ),
    },
)

edited_tournois = editor_df_to_tournois(edited_df)
validation_errors = validate_tournois(edited_tournois)

with chart_container:
    if edited_tournois and not validation_errors:
        try:
            fig, _ = build_chart(edited_tournois)
        except ValueError as error:
            st.error(str(error))
        else:
            st.plotly_chart(fig, width="stretch")
    elif not edited_tournois:
        st.info("Ajoute un tournoi dans le tableau pour afficher le planning.")

if validation_errors:
    for error in validation_errors:
        st.error(error)

actions = st.container(horizontal=True)

if actions.button("Enregistrer", type="primary", icon=":material/save:"):
    if validation_errors:
        st.error("Corrige les erreurs avant d'enregistrer.")
    else:
        save_tournois(edited_tournois)
        st.session_state.tournois = edited_tournois
        st.success("Tournois enregistrés dans tournois.json.")

if actions.button("Recharger depuis le fichier", icon=":material/refresh:"):
    st.session_state.tournois = load_tournois()
    st.session_state.tournois_editor_version += 1
    st.rerun()
