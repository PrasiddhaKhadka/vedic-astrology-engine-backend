"""
AstroGyan API — OpenAPI schema definitions using drf-spectacular.
Import these decorators and apply them to your views.py functions.
"""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_field,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from rest_framework import serializers

# ─────────────────────────────────────────────
# Shared inline serializers (for docs only)
# ─────────────────────────────────────────────

BirthDataSchema = inline_serializer(
    name="BirthData",
    fields={
        "year":       serializers.IntegerField(help_text="Birth year (e.g. 1998)"),
        "month":      serializers.IntegerField(help_text="Birth month 1–12"),
        "day":        serializers.IntegerField(help_text="Birth day 1–31"),
        "hour":       serializers.IntegerField(help_text="Birth hour 0–23 (local time)"),
        "minute":     serializers.IntegerField(help_text="Birth minute 0–59"),
        "latitude":   serializers.FloatField(help_text="Birth latitude  (e.g. 27.7172 for Kathmandu)"),
        "longitude":  serializers.FloatField(help_text="Birth longitude (e.g. 85.3240 for Kathmandu)"),
        "utc_offset": serializers.FloatField(help_text="UTC offset in hours (e.g. 5.75 for NPT = UTC+5:45)"),
        "house_system": serializers.ChoiceField(
            choices=["whole_sign", "placidus", "equal", "koch"],
            default="whole_sign",
            help_text="House system. Whole Sign is the Vedic default.",
        ),
    },
)

_BIRTH_EXAMPLE_KTM = {
    "year": 1998, "month": 5, "day": 10,
    "hour": 10, "minute": 30,
    "latitude": 27.7172, "longitude": 85.3240,
    "utc_offset": 5.75,
    "house_system": "whole_sign",
}

# ─────────────────────────────────────────────
# Phase 1
# ─────────────────────────────────────────────

planet_positions_schema = extend_schema(
    tags=["Phase 1 — Planets & Houses"],
    summary="Planet Positions",
    description=(
        "Returns sidereal (Vedic/Lahiri) positions of all **9 Jyotish grahas**: "
        "Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.\n\n"
        "Each planet returns: `longitude` (0–360°), `latitude`, `speed` (deg/day), "
        "`retrograde` (bool), `rasi` (zodiac sign name), `degree_in_rasi`."
    ),
    request=BirthDataSchema,
    examples=[
        OpenApiExample(
            "Kathmandu birth",
            value=_BIRTH_EXAMPLE_KTM,
            request_only=True,
        ),
        OpenApiExample(
            "Success response",
            value={
                "status": "success",
                "ayanamsa": "Lahiri",
                "system": "Vedic (Sidereal)",
                "planets": {
                    "sun":  {"longitude": 25.499, "rasi": "Aries",  "degree_in_rasi": 25.499, "retrograde": False, "speed": 0.966},
                    "moon": {"longitude": 189.81, "rasi": "Libra",  "degree_in_rasi": 9.81,  "retrograde": False, "speed": 11.95},
                    "rahu": {"longitude": 133.05, "rasi": "Leo",    "degree_in_rasi": 13.05, "retrograde": True,  "speed": -0.053},
                    "ketu": {"longitude": 313.05, "rasi": "Aquarius","degree_in_rasi": 13.05,"retrograde": True,  "speed": -0.053},
                },
            },
            response_only=True,
        ),
    ],
    responses={
        200: OpenApiResponse(description="Planet positions in all 9 grahas"),
        400: OpenApiResponse(description="Validation error — invalid birth data"),
    },
)

ascendant_houses_schema = extend_schema(
    tags=["Phase 1 — Planets & Houses"],
    summary="Ascendant + Houses",
    description=(
        "Returns the **Ascendant (Lagna)**, Midheaven, and all **12 house cusps**.\n\n"
        "Supported house systems: `whole_sign` (Vedic default), `placidus`, `equal`, `koch`."
    ),
    request=BirthDataSchema,
    examples=[
        OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True),
    ],
    responses={
        200: OpenApiResponse(description="Ascendant and 12 house cusps"),
        400: OpenApiResponse(description="Validation error"),
    },
)

full_chart_schema = extend_schema(
    tags=["Phase 1 — Planets & Houses"],
    summary="Full Chart (Planets + Houses) ⭐",
    description=(
        "**Most-used endpoint.** Returns both planet positions *and* house cusps in a single call. "
        "Ideal for chart rendering UIs.\n\n"
        "Ayanamsa: **Lahiri** | System: **Vedic Sidereal**"
    ),
    request=BirthDataSchema,
    examples=[
        OpenApiExample("Kathmandu birth (Whole Sign)", value=_BIRTH_EXAMPLE_KTM, request_only=True),
        OpenApiExample("Mumbai birth (Placidus)", value={**_BIRTH_EXAMPLE_KTM, "latitude": 19.0760, "longitude": 72.8777, "utc_offset": 5.5, "house_system": "placidus"}, request_only=True),
        OpenApiExample(
            "Success response",
            value={
                "status": "success",
                "ayanamsa": "Lahiri",
                "system": "Vedic (Sidereal)",
                "ascendant": {"longitude": 95.77, "rasi": "Cancer", "rasi_index": 3, "degree_in_rasi": 5.77},
                "midheaven":  {"longitude": 358.45, "rasi": "Pisces", "rasi_index": 11, "degree_in_rasi": 28.45},
                "houses": [
                    {"house": 1, "cusp_longitude": 90.0, "rasi": "Cancer", "rasi_index": 3, "degree_in_rasi": 0.0},
                    {"house": 2, "cusp_longitude": 120.0, "rasi": "Leo",   "rasi_index": 4, "degree_in_rasi": 0.0},
                ],
                "house_system": "whole_sign",
                "planets": {
                    "sun": {"longitude": 25.499, "rasi": "Aries", "degree_in_rasi": 25.499, "retrograde": False},
                },
            },
            response_only=True,
        ),
    ],
    responses={
        200: OpenApiResponse(description="Full chart: planets + houses"),
        400: OpenApiResponse(description="Validation error"),
    },
)

# ─────────────────────────────────────────────
# Phase 2
# ─────────────────────────────────────────────

nakshatra_schema = extend_schema(
    tags=["Phase 2 — Nakshatra, Panchang & Dasha"],
    summary="Nakshatra",
    description=(
        "Returns the Moon's **Nakshatra**, **Pada** (1–4), Nakshatra lord, "
        "and the exact Moon longitude at birth."
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="Nakshatra details"), 400: OpenApiResponse(description="Validation error")},
)

panchang_schema = extend_schema(
    tags=["Phase 2 — Nakshatra, Panchang & Dasha"],
    summary="Panchang",
    description=(
        "Returns all **5 Panchang elements** for the birth moment:\n\n"
        "| Element | Description |\n"
        "|---------|-------------|\n"
        "| **Tithi** | Lunar day (1–30) |\n"
        "| **Vara** | Weekday (Sun–Sat) |\n"
        "| **Nakshatra** | Moon's asterism |\n"
        "| **Yoga** | Sun+Moon longitude ÷ 13.333° |\n"
        "| **Karana** | Half-tithi |\n"
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="Five Panchang elements"), 400: OpenApiResponse(description="Validation error")},
)

dasha_schema = extend_schema(
    tags=["Phase 2 — Nakshatra, Panchang & Dasha"],
    summary="Vimshottari Mahadasha",
    description=(
        "Returns **Vimshottari Mahadasha** (major periods) for 120 years from birth.\n\n"
        "Each period includes: planet lord, start date, end date, duration in years."
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="120-year Mahadasha timeline"), 400: OpenApiResponse(description="Validation error")},
)

# ─────────────────────────────────────────────
# Phase 3
# ─────────────────────────────────────────────

antardasha_schema = extend_schema(
    tags=["Phase 3 — Advanced Chart Analysis"],
    summary="Antardasha (Sub-periods)",
    description=(
        "Returns Vimshottari **Mahadasha with nested Antardasha** (Bhukti) sub-periods. "
        "Each Mahadasha is subdivided into 9 Antardashas proportional to the 120-year cycle."
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="Dasha–Antardasha tree"), 400: OpenApiResponse(description="Validation error")},
)

divisional_chart_schema = extend_schema(
    tags=["Phase 3 — Advanced Chart Analysis"],
    summary="Divisional Chart (Varga)",
    description=(
        "Returns a **divisional chart** (Varga) for the given division number.\n\n"
        "| D | Name | Signifies |\n"
        "|---|------|----------|\n"
        "| 2 | D2 Hora | Wealth |\n"
        "| 3 | D3 Drekkana | Siblings |\n"
        "| 7 | D7 Saptamsha | Children |\n"
        "| 9 | D9 Navamsa | Spouse / Dharma |\n"
        "| 10 | D10 Dashamsa | Career |\n"
        "| 12 | D12 Dwadashamsa | Parents |\n"
        "| 16 | D16 Shodashamsa | Vehicles |\n"
        "| 30 | D30 Trimsamsa | Misfortune |\n"
        "| 60 | D60 Shashtiamsa | Past karma |\n\n"
        "Pass `division` in the request body (default: `9`)."
    ),
    request=inline_serializer(
        name="DivisionalChartRequest",
        fields={
            **{k: BirthDataSchema.fields[k] for k in BirthDataSchema.fields},
            "division": serializers.ChoiceField(
                choices=[2, 3, 7, 9, 10, 12, 16, 30, 60],
                default=9,
                help_text="Varga division number",
            ),
        },
    ),
    examples=[
        OpenApiExample("D9 Navamsa", value={**_BIRTH_EXAMPLE_KTM, "division": 9}, request_only=True),
        OpenApiExample("D10 Dashamsa (Career)", value={**_BIRTH_EXAMPLE_KTM, "division": 10}, request_only=True),
    ],
    responses={200: OpenApiResponse(description="Divisional chart planets"), 400: OpenApiResponse(description="Invalid division or birth data")},
)

yogas_schema = extend_schema(
    tags=["Phase 3 — Advanced Chart Analysis"],
    summary="Vedic Yogas",
    description=(
        "Detects major **Vedic Yogas** in the birth chart:\n\n"
        "- **Pancha Mahapurusha Yogas** (Ruchaka, Bhadra, Hamsa, Malavya, Shasha)\n"
        "- Gajakesari, Budha-Aditya, Chandra-Mangala\n"
        "- Dhana Yoga (wealth combinations)\n"
        "- Kemadruma Yoga (isolation)\n"
        "- Neecha Bhanga Raja Yoga (debilitation cancellation)\n\n"
        "Each yoga returns: `present` (bool), `strength`, `description`."
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="List of active and inactive yogas"), 400: OpenApiResponse(description="Validation error")},
)

ashtakavarga_schema = extend_schema(
    tags=["Phase 3 — Advanced Chart Analysis"],
    summary="Ashtakavarga",
    description=(
        "Returns **Ashtakavarga** bindus (points) for each planet across all 12 signs, "
        "plus the combined **Sarvashtakavarga** totals.\n\n"
        "**Score interpretation:**\n"
        "- Planet: ≥ 5 = Strong, 3–4 = Moderate, < 3 = Weak\n"
        "- Sarva: ≥ 30 = Strong sign, 25–29 = Moderate, < 25 = Weak"
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="Ashtakavarga scores per sign"), 400: OpenApiResponse(description="Validation error")},
)

# ─────────────────────────────────────────────
# Phase 4
# ─────────────────────────────────────────────

_COMPATIBILITY_EXAMPLE = {
    "boy": {**_BIRTH_EXAMPLE_KTM},
    "girl": {
        "year": 2000, "month": 3, "day": 15,
        "hour": 8, "minute": 0,
        "latitude": 28.6139, "longitude": 77.2090,
        "utc_offset": 5.5,
        "house_system": "whole_sign",
    },
}

CompatibilitySchema = inline_serializer(
    name="CompatibilityRequest",
    fields={
        "boy":  BirthDataSchema,
        "girl": BirthDataSchema,
    },
)

guna_milan_schema = extend_schema(
    tags=["Phase 4 — Compatibility"],
    summary="Guna Milan (Ashtakoot)",
    description=(
        "Calculates **36-point Ashtakoot Guna Milan** (traditional Vedic compatibility matching).\n\n"
        "| Koot | Max Points | Signifies |\n"
        "|------|-----------|----------|\n"
        "| Varna | 1 | Spiritual compatibility |\n"
        "| Vashya | 2 | Dominance |\n"
        "| Tara | 3 | Birth star |\n"
        "| Yoni | 4 | Intimacy |\n"
        "| Graha Maitri | 5 | Mental compatibility |\n"
        "| Gana | 6 | Temperament |\n"
        "| Rashi / Bhakoot | 7 | Destiny |\n"
        "| Nadi | 8 | Health & progeny |\n\n"
        "**Score interpretation:** 36 = Perfect, ≥ 18 = Recommended, < 18 = Not recommended."
    ),
    request=CompatibilitySchema,
    examples=[OpenApiExample("Boy (Kathmandu) + Girl (Delhi)", value=_COMPATIBILITY_EXAMPLE, request_only=True)],
    responses={200: OpenApiResponse(description="Guna points per Koot + total"), 400: OpenApiResponse(description="Invalid birth data")},
)

mangal_dosha_schema = extend_schema(
    tags=["Phase 4 — Compatibility"],
    summary="Mangal Dosha Check",
    description=(
        "Checks **Mangal Dosha** (Kuja Dosha) for both partners.\n\n"
        "Mars in houses **1, 2, 4, 7, 8, or 12** from Lagna, Moon, or Venus causes Mangal Dosha. "
        "When **both** partners have it, the doshas cancel each other in most traditions.\n\n"
        "Returns: `has_mangal_dosha`, `mars_house`, `severity`, `cancellation_factors`."
    ),
    request=CompatibilitySchema,
    examples=[OpenApiExample("Boy + Girl", value=_COMPATIBILITY_EXAMPLE, request_only=True)],
    responses={200: OpenApiResponse(description="Mangal Dosha status for both + cancellation"), 400: OpenApiResponse(description="Invalid birth data")},
)

# ─────────────────────────────────────────────
# Phase 5
# ─────────────────────────────────────────────

transits_current_schema = extend_schema(
    tags=["Phase 5 — Transits"],
    summary="Current Transits vs Natal Chart",
    description=(
        "Shows where all planets are **right now** vs your natal chart.\n\n"
        "Returns for each transiting planet:\n"
        "- House in natal chart it currently occupies\n"
        "- Effect description\n"
        "- **Ashtakavarga score** in that sign\n"
        "- **Sade Sati** phase check (if applicable)\n"
        "- Conjunctions with natal planets (within 5°)"
    ),
    request=BirthDataSchema,
    examples=[OpenApiExample("Kathmandu birth", value=_BIRTH_EXAMPLE_KTM, request_only=True)],
    responses={200: OpenApiResponse(description="Live transit analysis vs natal chart"), 400: OpenApiResponse(description="Validation error")},
)

transits_date_schema = extend_schema(
    tags=["Phase 5 — Transits"],
    summary="Transits for a Specific Date",
    description=(
        "Same as Current Transits but for **any date you specify**. "
        "Useful for predictive planning.\n\n"
        "Extra required fields: `transit_year`, `transit_month`, `transit_day`.\n"
        "Optional: `transit_hour` (default 12), `transit_minute` (default 0)."
    ),
    request=inline_serializer(
        name="TransitsDateRequest",
        fields={
            **{k: BirthDataSchema.fields[k] for k in BirthDataSchema.fields},
            "transit_year":   serializers.IntegerField(help_text="Year of the transit date"),
            "transit_month":  serializers.IntegerField(help_text="Month of the transit date"),
            "transit_day":    serializers.IntegerField(help_text="Day of the transit date"),
            "transit_hour":   serializers.IntegerField(default=12, required=False, help_text="Hour (default 12)"),
            "transit_minute": serializers.IntegerField(default=0,  required=False, help_text="Minute (default 0)"),
        },
    ),
    examples=[
        OpenApiExample(
            "June 15 2026",
            value={
                **_BIRTH_EXAMPLE_KTM,
                "transit_year": 2026, "transit_month": 6,
                "transit_day": 15,   "transit_hour": 12, "transit_minute": 0,
            },
            request_only=True,
        ),
    ],
    responses={200: OpenApiResponse(description="Transit analysis for the given date"), 400: OpenApiResponse(description="Validation error")},
)

transits_moon_schema = extend_schema(
    tags=["Phase 5 — Transits"],
    summary="Moon Transit (Chandra Gochar)",
    description=(
        "Current **Chandra Gochar** — Moon's transit details.\n\n"
        "Returns:\n"
        "- Current Rasi & Nakshatra (+ Pada)\n"
        "- Nakshatra lord\n"
        "- Moon speed (deg/day)\n"
        "- Degrees remaining in current sign\n"
        "- **Hours to next sign change**\n"
        "- Next Rasi name\n\n"
        "No birth data required. Optionally pass `transit_year/month/day` for a future date. "
        "Moon changes sign every ~2.25 days — great for **daily horoscope apps**."
    ),
    request=inline_serializer(
        name="MoonTransitRequest",
        fields={
            "transit_year":   serializers.IntegerField(required=False, help_text="Optional — defaults to NOW"),
            "transit_month":  serializers.IntegerField(required=False),
            "transit_day":    serializers.IntegerField(required=False),
            "transit_hour":   serializers.IntegerField(required=False, default=12),
            "transit_minute": serializers.IntegerField(required=False, default=0),
        },
    ),
    examples=[
        OpenApiExample("Current Moon (no body needed)", value={}, request_only=True),
        OpenApiExample(
            "Moon on Jun 15 2026",
            value={"transit_year": 2026, "transit_month": 6, "transit_day": 15},
            request_only=True,
        ),
        OpenApiExample(
            "Success — Moon in Capricorn",
            value={
                "status": "success",
                "ayanamsa": "Lahiri",
                "moon_longitude": 275.703,
                "rasi": "Capricorn",
                "rasi_index": 9,
                "degree_in_rasi": 5.703,
                "nakshatra": "Uttara Ashadha",
                "nakshatra_lord": "Sun",
                "pada": 3,
                "speed_deg_per_day": 12.47,
                "degrees_to_next_sign": 24.30,
                "hours_to_next_sign": 46.8,
                "next_rasi": "Aquarius",
            },
            response_only=True,
        ),
    ],
    responses={200: OpenApiResponse(description="Moon transit details"), 400: OpenApiResponse(description="Invalid transit date")},
)