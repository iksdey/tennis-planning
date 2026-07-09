import holidays
import pandas as pd


DATE_FORMAT_FR = "%d/%m/%Y"
TYPE_CLASSIQUE = "classique"
TYPE_TMC = "TMC"

JOURS_FERIES_FRANCE = holidays.country_holidays(
    "FR",
    observed=False,
)


def parse_date_fr(date_value):
    if date_value is None:
        return pd.NaT

    if isinstance(date_value, str):
        date_value = date_value.strip()
        if not date_value:
            return pd.NaT

        return pd.to_datetime(date_value, format=DATE_FORMAT_FR)

    if pd.isna(date_value):
        return pd.NaT

    return pd.to_datetime(date_value)


def est_tmc(type_tournoi):
    return str(type_tournoi).strip().upper() == TYPE_TMC


def est_classique(type_tournoi):
    return str(type_tournoi).strip().lower() == TYPE_CLASSIQUE


def couleur_barre_tournoi(
    type_tournoi,
    couleur_classique,
    couleur_tmc,
):
    if est_tmc(type_tournoi):
        return couleur_tmc

    return couleur_classique


def tournois_classiques(df):
    return df[df["type"].apply(est_classique)].copy()


def normaliser_dates_tournois(
    df,
    colonnes_dates=("debut", "fin", "entree_reelle"),
):
    df = df.copy()

    for colonne in colonnes_dates:
        if colonne in df.columns:
            df[colonne] = df[colonne].apply(parse_date_fr)

    return df


def preparer_tournois(
    df,
    classement_joueur,
    ponderation_jours,
    couleur_classique,
    couleur_tmc,
):
    df = normaliser_dates_tournois(df)

    df["couleur_barre"] = df["type"].apply(
        lambda type_tournoi: couleur_barre_tournoi(
            type_tournoi,
            couleur_classique,
            couleur_tmc,
        )
    )

    df["tours_avant_entree"] = pd.NA
    df["debut_participation"] = pd.NaT

    masque_classique = df["type"].apply(est_classique)

    df.loc[masque_classique, "tours_avant_entree"] = df.loc[
        masque_classique
    ].apply(
        lambda row: nombre_tours_avant_entree(
            row["classement_min"],
            row["classement_max"],
            classement_joueur,
        ),
        axis=1,
    )

    df.loc[masque_classique, "debut_participation"] = df.loc[
        masque_classique
    ].apply(
        lambda row: date_entree_ponderee(
            row["debut"],
            row["tours_avant_entree"],
            ponderation_jours,
        ),
        axis=1,
    )

    return df


def nombre_tours_avant_entree(
    classement_min,
    classement_max,
    classement_joueur
):

    classements = [
        "NC", "40", "30/5", "30/4", "30/3", "30/2", "30/1", "30",
        "15/5", "15/4", "15/3", "15/2", "15/1", "15",
        "5/6", "4/6", "3/6", "2/6", "1/6", "0",
        "-2/6", "-4/6", "-15"
    ]

    rang_min = classements.index(classement_min)
    rang_max = classements.index(classement_max)
    rang_joueur = classements.index(classement_joueur)

    if not rang_min <= rang_joueur <= rang_max:
        raise ValueError("Le classement du joueur est hors des limites du tournoi.")

    rang_premier_tour = classements.index("30/5")

    tour_min = max(1, rang_min - rang_premier_tour + 1)
    tour_joueur = max(1, rang_joueur - rang_premier_tour + 1)

    nombre_tours = tour_joueur - tour_min + 1

    return nombre_tours


def date_entree_ponderee(
    date_debut_tournoi,
    nombre_tours,
    ponderation_jours,
):
    date = parse_date_fr(date_debut_tournoi)
    tours_cumules = 0.0

    while tours_cumules < nombre_tours:
        date += pd.Timedelta(days=1)
        jour = date.day_name(locale="fr_FR").lower()

        if date.date() in JOURS_FERIES_FRANCE:
            jour = "ferie"

        tours_cumules += ponderation_jours[jour]

    return date
