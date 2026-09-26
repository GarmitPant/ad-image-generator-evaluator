"""Country facts, not a country-by-season scenario registry."""

from .contracts import Geography, Season

FACTS = {
    "US": (
        "United States",
        "north",
        "temperate",
        "varied regional settings; avoid assuming a specific state",
    ),
    "GB": (
        "United Kingdom",
        "north",
        "temperate",
        "maritime climate; understated contemporary settings",
    ),
    "DE": ("Germany", "north", "temperate", "central European settings; regional variation"),
    "JP": ("Japan", "north", "temperate", "regional variation; ordinary contemporary environments"),
    "IN": (
        "India",
        "north",
        "tropical",
        "strong regional and monsoon variation; avoid nationwide weather claims",
    ),
    "AU": (
        "Australia",
        "south",
        "temperate",
        "strong regional variation; no iconic wildlife shortcuts",
    ),
    "BR": (
        "Brazil",
        "south",
        "tropical",
        "strong regional variation; avoid nationwide weather claims",
    ),
    "AE": (
        "United Arab Emirates",
        "north",
        "arid",
        "arid climate; contemporary settings; no religious decor",
    ),
}
MONTHS = {"spring": [3, 4, 5], "summer": [6, 7, 8], "autumn": [9, 10, 11], "winter": [12, 1, 2]}


def resolve_context(geography: Geography, season: Season):
    name, hemisphere, band, note = FACTS[geography.value]
    months = MONTHS[season.value]
    if hemisphere == "south":
        months = [((month + 5) % 12) + 1 for month in months]
    avoid = (
        ["snow", "snowfall", "frost", "blizzard"]
        if season.value == "summer" or band in {"tropical", "arid"}
        else []
    )
    return {
        "geography": geography.value,
        "country_name": name,
        "season": season.value,
        "hemisphere": hemisphere,
        "climate_band": band,
        "months": months,
        "context_note": note,
        "avoid_terms": avoid,
        "limitation": "Country-level pilot approximation; not a local weather assertion.",
    }
