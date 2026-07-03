import holidays
import pandas as pd


JOURS_FERIES_FRANCE = holidays.country_holidays(
    "FR",
    observed=False,
)


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
    date = pd.Timestamp(date_debut_tournoi)
    tours_cumules = 0.0

    while tours_cumules < nombre_tours:
        date += pd.Timedelta(days=1)
        jour = date.day_name(locale="fr_FR").lower()

        if date.date() in JOURS_FERIES_FRANCE:
            jour = "ferie"

        tours_cumules += ponderation_jours[jour]

    return date
