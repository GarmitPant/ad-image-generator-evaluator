"""Country facts, not a country-by-season scenario registry."""

from .contracts import Geography, Season

# Objective facts plus a neutral style note. Notes invite a specific city/region; they do not list
# cues, so adding a country stays one row (no per-country or per-season scene registry).
REGION_NOTE = "choose a specific city or region and make it recognisable through regional design"
FACTS = {
    "US": ("United States", "north", "temperate", "large regional variety; " + REGION_NOTE),
    "GB": ("United Kingdom", "north", "temperate", "maritime climate; " + REGION_NOTE),
    "DE": ("Germany", "north", "temperate", "central European climate; " + REGION_NOTE),
    "JP": ("Japan", "north", "temperate", "strong seasonal contrast; " + REGION_NOTE),
    "IN": ("India", "north", "tropical", "monsoon June-September varies by region; " + REGION_NOTE),
    "AU": ("Australia", "south", "temperate", "large regional variety; " + REGION_NOTE),
    "BR": ("Brazil", "south", "tropical", "large regional variety; " + REGION_NOTE),
    "AE": ("United Arab Emirates", "north", "arid", "arid climate; " + REGION_NOTE),
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
