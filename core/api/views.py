from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from core.astro.calculator import RASI_NAMES, RASI_LORDS
from .serializers import BirthDataSerializer
from rest_framework.decorators import api_view, throttle_classes
from core.throttles import ChartThrottle, CompatibilityThrottle, TransitThrottle


from core.astro.calculator import (
    get_julian_day,
    get_planet_positions,
    get_ascendant_and_houses,
    get_nakshatra,
    get_panchang,
    get_vimshottari_dasha,
    get_antardasha,
    get_divisional_chart,
    get_yogas,
    get_ashtakavarga,
    calculate_ashtakoot,
    check_mangal_dosha,
    analyze_transits,
    get_sade_sati,
    get_moon_transit,
    get_current_jd,
    RASI_NAMES,
)


# ─── Reusable schema snippets ──────────────────────────────────────────────────

BIRTH_DATA_PROPERTIES = {
    'year':         {'type': 'integer', 'example': 1998, 'description': 'Birth year (1800–2100)'},
    'month':        {'type': 'integer', 'example': 5,    'description': 'Birth month (1–12)'},
    'day':          {'type': 'integer', 'example': 10,   'description': 'Birth day (1–31)'},
    'hour':         {'type': 'integer', 'example': 10,   'description': 'Local birth hour (0–23)'},
    'minute':       {'type': 'integer', 'example': 30,   'description': 'Birth minute (0–59)'},
    'latitude':     {'type': 'number',  'example': 27.7172,  'description': 'Birth latitude (-90 to 90)'},
    'longitude':    {'type': 'number',  'example': 85.3240,  'description': 'Birth longitude (-180 to 180)'},
    'utc_offset':   {'type': 'number',  'example': 5.75, 'description': 'UTC offset in hours. e.g. 5.75 = Nepal (NPT), 5.5 = India (IST), 0 = UTC'},
    'house_system': {
        'type': 'string',
        'example': 'whole_sign',
        'enum': ['whole_sign', 'placidus', 'equal', 'koch'],
        'description': 'House system. Defaults to whole_sign (standard for Vedic/Jyotish)',
    },
}

BIRTH_DATA_REQUIRED = ['year', 'month', 'day', 'hour', 'minute', 'latitude', 'longitude']

KATHMANDU_EXAMPLE = OpenApiExample(
    'Kathmandu — May 10, 1998',
    value={
        'year': 1998, 'month': 5, 'day': 10,
        'hour': 10,   'minute': 30,
        'latitude': 27.7172, 'longitude': 85.3240,
        'utc_offset': 5.75, 'house_system': 'whole_sign',
    },
    request_only=True,
)

MUMBAI_EXAMPLE = OpenApiExample(
    'Mumbai — Aug 15, 2000',
    value={
        'year': 2000, 'month': 8, 'day': 15,
        'hour': 6,    'minute': 0,
        'latitude': 19.0760, 'longitude': 72.8777,
        'utc_offset': 5.5, 'house_system': 'whole_sign',
    },
    request_only=True,
)

BIRTH_REQUEST_SCHEMA = {
    'application/json': {
        'type': 'object',
        'required': BIRTH_DATA_REQUIRED,
        'properties': BIRTH_DATA_PROPERTIES,
    }
}

ERROR_400 = OpenApiResponse(description='Validation error — missing or invalid fields')
ERROR_400_DIVISION = OpenApiResponse(description='Invalid division number. Must be one of: 2, 3, 7, 9, 10, 12, 16, 30, 60')


# ─── Helper ────────────────────────────────────────────────────────────────────

def parse_birth_data(request):
    """
    Validate request and convert local birth time → UTC Julian Day.
    Returns (validated_data, julian_day, errors).
    """
    serializer = BirthDataSerializer(data=request.data)
    if not serializer.is_valid():
        return None, None, serializer.errors

    d = serializer.validated_data

    utc_hour   = d['hour'] - d['utc_offset']
    utc_minute = d['minute']
    day        = d['day']
    month      = d['month']
    year       = d['year']

    if utc_hour < 0:
        utc_hour += 24
        day -= 1
        if day == 0:
            month -= 1
            if month == 0:
                month = 12
                year -= 1
            import calendar
            day = calendar.monthrange(year, month)[1]
    elif utc_hour >= 24:
        utc_hour -= 24
        day += 1
        import calendar
        if day > calendar.monthrange(year, month)[1]:
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1

    jd = get_julian_day(year, month, day, int(utc_hour), utc_minute)
    return d, jd, None


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — CHART
# ═══════════════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['Chart'],
    summary='Planet positions',
    description=(
        'Returns sidereal (Vedic/Lahiri ayanamsa) positions of all **9 Jyotish grahas**: '
        'Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, and Ketu.\n\n'
        'Each planet includes: ecliptic longitude, latitude, speed, retrograde flag, '
        'rasi (zodiac sign), and degree within that sign.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE, MUMBAI_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Successful response with all 9 planet positions',
            response={
                'type': 'object',
                'properties': {
                    'status':  {'type': 'string', 'example': 'success'},
                    'ayanamsa':{'type': 'string', 'example': 'Lahiri'},
                    'system':  {'type': 'string', 'example': 'Vedic (Sidereal)'},
                    'planets': {
                        'type': 'object',
                        'description': 'Keyed by planet name (sun, moon, mars, ...)',
                        'example': {
                            'sun': {
                                'longitude': 25.49901, 'latitude': 0.000142,
                                'speed': 0.966243, 'retrograde': False,
                                'rasi': 'Aries', 'rasi_index': 0, 'degree_in_rasi': 25.499,
                            }
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def planet_positions(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    positions = get_planet_positions(jd)

    return Response({
        'status':  'success',
        'ayanamsa':'Lahiri',
        'system':  'Vedic (Sidereal)',
        'planets': positions,
    })


@extend_schema(
    tags=['Chart'],
    summary='Ascendant and house cusps',
    description=(
        'Returns the **Ascendant (Lagna)** and all **12 house cusps** using the selected '
        'house system.\n\n'
        'Defaults to **Whole Sign** — the standard system for Vedic/Jyotish astrology. '
        'Placidus, Equal, and Koch are also supported for Western-style calculations.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE, MUMBAI_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Ascendant and 12 house cusps',
            response={
                'type': 'object',
                'properties': {
                    'status':      {'type': 'string', 'example': 'success'},
                    'ayanamsa':    {'type': 'string', 'example': 'Lahiri'},
                    'ascendant':   {
                        'type': 'object',
                        'example': {'longitude': 95.77, 'rasi': 'Cancer', 'rasi_index': 3, 'degree_in_rasi': 5.77},
                    },
                    'midheaven':   {'type': 'object', 'example': {'longitude': 358.45, 'rasi': 'Pisces'}},
                    'houses':      {
                        'type': 'array',
                        'description': '12 house objects with cusp longitude and rasi',
                        'example': [{'house': 1, 'cusp_longitude': 90.0, 'rasi': 'Cancer', 'rasi_index': 3, 'degree_in_rasi': 0.0}],
                    },
                    'house_system':{'type': 'string', 'example': 'whole_sign'},
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def ascendant_houses(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_ascendant_and_houses(jd, d['latitude'], d['longitude'], d['house_system'])

    return Response({
        'status':  'success',
        'ayanamsa':'Lahiri',
        'system':  'Vedic (Sidereal)',
        **result,
    })


@extend_schema(
    tags=['Chart'],
    summary='Full birth chart (planets + houses)',
    description=(
        'Combined endpoint — returns **planet positions AND house cusps** in a single call. '
        'This is the most commonly used endpoint for rendering a full Kundali/birth chart.\n\n'
        'Equivalent to calling `/planets/` and `/houses/` together.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE, MUMBAI_EXAMPLE],
    responses={
        200: OpenApiResponse(description='Full chart: planets + ascendant + 12 houses'),
        400: ERROR_400,
    },
)
@api_view(['POST'])
@throttle_classes([ChartThrottle])
def full_chart(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    planets = get_planet_positions(jd)
    houses  = get_ascendant_and_houses(jd, d['latitude'], d['longitude'], d['house_system'])

    return Response({
        'status':  'success',
        'ayanamsa':'Lahiri',
        'system':  'Vedic (Sidereal)',
        'planets': planets,
        **houses,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — PANCHANG & DASHA
# ═══════════════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['Panchang'],
    summary="Moon's Nakshatra, Pada and lord",
    description=(
        "Calculates the **Nakshatra** (lunar mansion) of the Moon at the time of birth, "
        "along with the **Pada** (quarter, 1–4), the **Nakshatra lord** (planet), "
        "and precise degree within the nakshatra.\n\n"
        "There are 27 Nakshatras, each spanning 13°20'. Each is ruled by a planet in "
        "Vimshottari order: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury."
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description="Moon's Nakshatra details",
            response={
                'type': 'object',
                'properties': {
                    'status':               {'type': 'string', 'example': 'success'},
                    'ayanamsa':             {'type': 'string', 'example': 'Lahiri'},
                    'nakshatra':            {'type': 'string', 'example': 'Swati'},
                    'nakshatra_index':      {'type': 'integer', 'example': 15, 'description': '1-based (1=Ashwini … 27=Revati)'},
                    'pada':                 {'type': 'integer', 'example': 1,  'description': 'Quarter within nakshatra (1–4)'},
                    'lord':                 {'type': 'string', 'example': 'Rahu'},
                    'moon_longitude':       {'type': 'number', 'example': 189.814505},
                    'degree_in_nakshatra':  {'type': 'number', 'example': 3.1478},
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def nakshatra(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_nakshatra(jd)

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **result})


@extend_schema(
    tags=['Panchang'],
    summary='Panchang — five elements of the day',
    description=(
        'Returns the **5 Panchang elements** for the birth date and time:\n\n'
        '| Element | Description |\n'
        '|---------|-------------|\n'
        '| **Tithi** | Lunar day (1–30), Shukla or Krishna Paksha |\n'
        '| **Vara** | Weekday (Sunday–Saturday) |\n'
        '| **Nakshatra** | Moon\'s lunar mansion |\n'
        '| **Yoga** | Sum of Sun+Moon longitude / 13.33° (27 yogas) |\n'
        '| **Karana** | Half of a Tithi — 11 Karanas |\n'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Five Panchang elements',
            response={
                'type': 'object',
                'properties': {
                    'status':   {'type': 'string', 'example': 'success'},
                    'tithi':    {
                        'type': 'object',
                        'example': {'name': 'Chaturdashi', 'paksha': 'Shukla', 'index': 14},
                    },
                    'vara':     {'type': 'object', 'example': {'name': 'Sunday', 'index': 0}},
                    'nakshatra':{'type': 'object', 'description': 'Same as /nakshatra/ response'},
                    'yoga':     {'type': 'object', 'example': {'name': 'Vyatipata', 'index': 17}},
                    'karana':   {'type': 'object', 'example': {'name': 'Vanija',    'index': 6}},
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def panchang(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_panchang(jd, d['latitude'], d['longitude'])

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **result})


@extend_schema(
    tags=['Dasha'],
    summary='Vimshottari Mahadasha periods',
    description=(
        'Returns all **9 Vimshottari Mahadasha** periods spanning 120 years from birth.\n\n'
        'The starting dasha lord and remaining years are calculated from the **Moon\'s Nakshatra** '
        'at birth. The sequence is always: Ketu(7) → Venus(20) → Sun(6) → Moon(10) → '
        'Mars(7) → Rahu(18) → Jupiter(16) → Saturn(19) → Mercury(17).\n\n'
        'Each period includes start date, end date, and duration in years.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Vimshottari Mahadasha list',
            response={
                'type': 'object',
                'properties': {
                    'status':         {'type': 'string', 'example': 'success'},
                    'system':         {'type': 'string', 'example': 'Vimshottari'},
                    'total_years':    {'type': 'integer','example': 120},
                    'moon_nakshatra': {'type': 'string', 'example': 'Swati'},
                    'mahadasha': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'lord':       {'type': 'string',  'example': 'Rahu'},
                                'start_date': {'type': 'string',  'example': '1998-05-10'},
                                'end_date':   {'type': 'string',  'example': '2012-02-08'},
                                'years':      {'type': 'number',  'example': 13.7504},
                            },
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def dasha(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_vimshottari_dasha(jd)

    return Response({'status': 'success', **result})


@extend_schema(
    tags=['Dasha'],
    summary='Mahadasha with nested Antardasha (sub-periods)',
    description=(
        'Returns all **9 Mahadashas**, each with **9 Antardashas (sub-periods)** nested inside.\n\n'
        'Antardasha duration formula: `(mahadasha_years × antardasha_years) / 120`\n\n'
        'The antardasha sequence within each mahadasha starts from the mahadasha lord itself '
        'and cycles through all 9 planets.\n\n'
        '⚠️ Response is large — consider caching on your frontend.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Mahadasha list with nested Antardasha',
            response={
                'type': 'object',
                'properties': {
                    'status':         {'type': 'string', 'example': 'success'},
                    'system':         {'type': 'string', 'example': 'Vimshottari'},
                    'moon_nakshatra': {'type': 'string', 'example': 'Swati'},
                    'mahadasha': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'lord':       {'type': 'string', 'example': 'Rahu'},
                                'start_date': {'type': 'string', 'example': '1998-05-10'},
                                'end_date':   {'type': 'string', 'example': '2012-02-08'},
                                'years':      {'type': 'number', 'example': 13.75},
                                'antardasha': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'lord':       {'type': 'string', 'example': 'Rahu'},
                                            'start_date': {'type': 'string', 'example': '1998-05-10'},
                                            'end_date':   {'type': 'string', 'example': '2001-01-17'},
                                            'years':      {'type': 'number', 'example': 2.6438},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
@throttle_classes([ChartThrottle])
def antardasha(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_antardasha(jd)

    return Response({'status': 'success', **result})


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — ADVANCED CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['Divisional'],
    summary='Divisional chart (D2 – D60)',
    description=(
        'Returns a **divisional (varga) chart** for the requested division.\n\n'
        '| Division | Chart Name   | Purpose |\n'
        '|----------|--------------|---------|\n'
        '| 2  | Hora         | Wealth and finances |\n'
        '| 3  | Drekkana     | Siblings and courage |\n'
        '| 7  | Saptamsa     | Children and progeny |\n'
        '| 9  | Navamsa      | Spouse, dharma, inner self — **most important** |\n'
        '| 10 | Dashamsa     | Career and profession |\n'
        '| 12 | Dwadashamsa  | Parents and ancestors |\n'
        '| 16 | Shodashamsa  | Vehicles and comforts |\n'
        '| 30 | Trimshamsa   | Misfortunes and health |\n'
        '| 60 | Shashtiamsa  | Detailed karma — most sensitive chart |\n\n'
        'Pass `"division": 9` in the request body for D9 Navamsa (default).'
    ),
    request={
        'application/json': {
            'type': 'object',
            'required': BIRTH_DATA_REQUIRED,
            'properties': {
                **BIRTH_DATA_PROPERTIES,
                'division': {
                    'type': 'integer',
                    'example': 9,
                    'enum': [2, 3, 7, 9, 10, 12, 16, 30, 60],
                    'description': 'Division number. Defaults to 9 (Navamsa).',
                },
            },
        }
    },
    examples=[
        OpenApiExample('D9 Navamsa — Kathmandu', value={
            'year': 1998, 'month': 5, 'day': 10,
            'hour': 10, 'minute': 30,
            'latitude': 27.7172, 'longitude': 85.3240,
            'utc_offset': 5.75, 'house_system': 'whole_sign',
            'division': 9,
        }, request_only=True),
        OpenApiExample('D10 Dashamsa — Career', value={
            'year': 1998, 'month': 5, 'day': 10,
            'hour': 10, 'minute': 30,
            'latitude': 27.7172, 'longitude': 85.3240,
            'utc_offset': 5.75, 'house_system': 'whole_sign',
            'division': 10,
        }, request_only=True),
    ],
    responses={
        200: OpenApiResponse(
            description='Divisional chart positions for all planets',
            response={
                'type': 'object',
                'properties': {
                    'status':     {'type': 'string', 'example': 'success'},
                    'division':   {'type': 'integer', 'example': 9},
                    'chart_name': {'type': 'string',  'example': 'Navamsa'},
                    'purpose':    {'type': 'string',  'example': 'Spouse, dharma, inner self'},
                    'ascendant':  {
                        'type': 'object',
                        'example': {'rasi': 'Scorpio', 'rasi_index': 7, 'lord': 'Mars'},
                    },
                    'planets': {
                        'type': 'object',
                        'description': 'Planet name → divisional rasi placement',
                        'example': {
                            'sun': {
                                'rasi': 'Leo', 'rasi_index': 4, 'lord': 'Sun',
                                'original_longitude': 25.499, 'original_rasi': 'Aries',
                                'degree_in_rasi': 25.499,
                            }
                        },
                    },
                },
            },
        ),
        400: ERROR_400_DIVISION,
    },
)
@api_view(['POST'])
def divisional_chart(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    division = request.data.get('division', 9)
    try:
        division = int(division)
        if division not in [2, 3, 7, 9, 10, 12, 16, 30, 60]:
            raise ValueError
    except (ValueError, TypeError):
        return Response(
            {'errors': {'division': 'Must be one of: 2, 3, 7, 9, 10, 12, 16, 30, 60'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = get_divisional_chart(jd, division)

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **result})


@extend_schema(
    tags=['Yogas'],
    summary='Detect Vedic yogas in birth chart',
    description=(
        'Detects major **Vedic Yogas** present in the birth chart.\n\n'
        '**Yogas detected:**\n'
        '- **Pancha Mahapurusha Yogas** — Ruchaka, Bhadra, Hamsa, Malavya, Shasha\n'
        '- **Gajakesari Yoga** — Jupiter in kendra from Moon\n'
        '- **Budha-Aditya Yoga** — Sun + Mercury conjunction\n'
        '- **Chandra-Mangala Yoga** — Moon + Mars conjunction or opposition\n'
        '- **Dhana Yoga** — Lords of wealth houses connecting with fortune houses\n'
        '- **Kemadruma Yoga** — Moon isolated (no planets in 2nd or 12th)\n'
        '- **Neecha Bhanga Raja Yoga** — Cancellation of debilitation\n\n'
        'Each yoga includes type (Benefic/Malefic/Mixed), description, and involved planets.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='List of yogas found in the birth chart',
            response={
                'type': 'object',
                'properties': {
                    'status':         {'type': 'string',  'example': 'success'},
                    'ascendant_rasi': {'type': 'string',  'example': 'Cancer'},
                    'yogas_found':    {'type': 'integer', 'example': 3},
                    'yogas': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name':        {'type': 'string', 'example': 'Gajakesari Yoga'},
                                'type':        {'type': 'string', 'example': 'Benefic'},
                                'description': {'type': 'string', 'example': 'Jupiter in kendra from Moon. Grants intelligence, fame, and prosperity.'},
                                'planets':     {'type': 'array',  'items': {'type': 'string'}, 'example': ['Jupiter', 'Moon']},
                            },
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
def yogas(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_yogas(jd, d['latitude'], d['longitude'])

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **result})


@extend_schema(
    tags=['Ashtakavarga'],
    summary='Ashtakavarga planetary strength scores',
    description=(
        'Returns **Bhinnashtakavarga** (individual planet grids) and **Sarvashtakavarga** '
        '(combined totals) scores across all 12 signs.\n\n'
        'Based on Brihat Parashara Hora Shastra (BPHS) tables. Each of the 7 planets + '
        'Lagna contributes bindus (points) to signs.\n\n'
        '**Score interpretation:**\n'
        '- Planet score ≥ 5 = **Strong** | 3–4 = **Moderate** | < 3 = **Weak**\n'
        '- Sarva score ≥ 30 = **Strong sign** | 25–29 = **Moderate** | < 25 = **Weak**\n\n'
        'Used for transit analysis — a planet transiting a sign with high Ashtakavarga '
        'score gives better results.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Bhinnashtakavarga and Sarvashtakavarga scores',
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'bhinnashtakavarga': {
                        'type': 'object',
                        'description': 'Per-planet scores across 12 signs',
                        'example': {
                            'sun': {
                                'scores': [5, 4, 3, 6, 5, 4, 3, 5, 4, 3, 6, 5],
                                'total': 48,
                                'signs': [{'rasi': 'Aries', 'score': 5, 'strength': 'Strong'}],
                            }
                        },
                    },
                    'sarvashtakavarga': {
                        'type': 'object',
                        'description': 'Combined totals across all 7 planets',
                        'example': {
                            'scores': [28, 25, 30, 33, 27, 26, 29, 31, 24, 28, 35, 31],
                            'total': 337,
                            'signs': [{'rasi': 'Aries', 'score': 28, 'strength': 'Moderate'}],
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
@throttle_classes([ChartThrottle])
def ashtakavarga(request):
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_ashtakavarga(jd, d['latitude'], d['longitude'])

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **result})


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — COMPATIBILITY (KUNDALI MILAN)
# ═══════════════════════════════════════════════════════════════════════════════

PARTNER_REQUEST_SCHEMA = {
    'application/json': {
        'type': 'object',
        'required': ['boy', 'girl'],
        'properties': {
            'boy':  {
                'type': 'object',
                'description': "Boy's birth data",
                'required': BIRTH_DATA_REQUIRED,
                'properties': BIRTH_DATA_PROPERTIES,
            },
            'girl': {
                'type': 'object',
                'description': "Girl's birth data",
                'required': BIRTH_DATA_REQUIRED,
                'properties': BIRTH_DATA_PROPERTIES,
            },
        },
    }
}

PARTNER_EXAMPLE = OpenApiExample(
    'Kathmandu boy + Mumbai girl',
    value={
        'boy': {
            'year': 1998, 'month': 5, 'day': 10,
            'hour': 10, 'minute': 30,
            'latitude': 27.7172, 'longitude': 85.3240,
            'utc_offset': 5.75, 'house_system': 'whole_sign',
        },
        'girl': {
            'year': 2000, 'month': 8, 'day': 15,
            'hour': 6, 'minute': 0,
            'latitude': 19.0760, 'longitude': 72.8777,
            'utc_offset': 5.5, 'house_system': 'whole_sign',
        },
    },
    request_only=True,
)


@extend_schema(
    tags=['Compatibility'],
    summary='36-point Ashtakoot Guna Milan',
    description=(
        'Calculates the classical **36-point Ashtakoot Guna matching** between two people.\n\n'
        '**The 8 Kootas (compatibility factors):**\n\n'
        '| Koota | Max | Measures |\n'
        '|-------|-----|----------|\n'
        '| Varna | 1 | Spiritual / ego compatibility |\n'
        '| Vasya | 2 | Mutual attraction and dominance |\n'
        '| Tara  | 3 | Destiny and health after marriage |\n'
        '| Yoni  | 4 | Physical and intimate compatibility |\n'
        '| Graha Maitri | 5 | Mental compatibility and friendship |\n'
        '| Gana  | 6 | Temperament (Deva / Manushya / Rakshasa) |\n'
        '| Bhakoot | 7 | Emotional and family well-being |\n'
        '| Nadi  | 8 | Health, progeny, genetic compatibility — **most critical** |\n\n'
        '**Score thresholds:** ≥32 = Excellent | ≥24 = Good | ≥18 = Average | <18 = Poor'
    ),
    request=PARTNER_REQUEST_SCHEMA,
    examples=[PARTNER_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Ashtakoot score with per-koota breakdown',
            response={
                'type': 'object',
                'properties': {
                    'status':          {'type': 'string',  'example': 'success'},
                    'boy_nakshatra':   {'type': 'string',  'example': 'Swati'},
                    'girl_nakshatra':  {'type': 'string',  'example': 'Dhanishta'},
                    'boy_rasi':        {'type': 'string',  'example': 'Libra'},
                    'girl_rasi':       {'type': 'string',  'example': 'Capricorn'},
                    'total_score':     {'type': 'number',  'example': 22},
                    'max_score':       {'type': 'integer', 'example': 36},
                    'percentage':      {'type': 'number',  'example': 61.1},
                    'compatibility':   {'type': 'string',  'example': 'Average'},
                    'recommendation':  {'type': 'string',  'example': 'Acceptable match — consult an astrologer'},
                    'kootas': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'koota':       {'type': 'string',  'example': 'Nadi'},
                                'max':         {'type': 'integer', 'example': 8},
                                'score':       {'type': 'number',  'example': 8},
                                'result':      {'type': 'string',  'example': 'Different Nadi — full score'},
                                'description': {'type': 'string',  'example': 'Health, progeny, and genetic compatibility.'},
                            },
                        },
                    },
                },
            },
        ),
        400: OpenApiResponse(description='Missing boy/girl data or validation error'),
    },
)
@api_view(['POST'])
@throttle_classes([CompatibilityThrottle])
def guna_milan(request):
    boy_data  = request.data.get('boy')
    girl_data = request.data.get('girl')

    if not boy_data or not girl_data:
        return Response(
            {'errors': 'Both "boy" and "girl" birth data are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    boy_serializer  = BirthDataSerializer(data=boy_data)
    girl_serializer = BirthDataSerializer(data=girl_data)

    errors = {}
    if not boy_serializer.is_valid():
        errors['boy'] = boy_serializer.errors
    if not girl_serializer.is_valid():
        errors['girl'] = girl_serializer.errors
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    b = boy_serializer.validated_data
    g = girl_serializer.validated_data

    jd_boy  = get_julian_day(b['year'], b['month'], b['day'],
                              int(b['hour'] - b['utc_offset']), b['minute'])
    jd_girl = get_julian_day(g['year'], g['month'], g['day'],
                              int(g['hour'] - g['utc_offset']), g['minute'])

    boy_nak  = get_nakshatra(jd_boy)
    girl_nak = get_nakshatra(jd_girl)
    result   = calculate_ashtakoot(jd_boy, jd_girl)

    return Response({
        'status':         'success',
        'boy_nakshatra':  boy_nak['nakshatra'],
        'girl_nakshatra': girl_nak['nakshatra'],
        'boy_rasi':       RASI_NAMES[int(boy_nak['moon_longitude'] / 30)],
        'girl_rasi':      RASI_NAMES[int(girl_nak['moon_longitude'] / 30)],
        **result,
    })


@extend_schema(
    tags=['Compatibility'],
    summary='Mangal Dosha check for both partners',
    description=(
        'Checks **Mangal Dosha (Kuja Dosha)** for both partners independently.\n\n'
        'Mars causes Mangal Dosha when placed in houses **1, 2, 4, 7, 8, or 12** '
        'from the Lagna. Checked from Lagna, Moon, and Venus.\n\n'
        '**Severity levels:**\n'
        '- `High` — Dosha from both Lagna and Moon\n'
        '- `Medium` — Dosha from Lagna or Moon\n'
        '- `None` — No dosha\n\n'
        '**Cancellations checked:** Mars in own sign (Aries/Scorpio) or exaltation (Capricorn), '
        'Jupiter aspecting Mars.\n\n'
        'If **both** partners have Mangal Dosha, `double_dosha_cancels: true` — '
        'most traditions consider this a cancellation.'
    ),
    request=PARTNER_REQUEST_SCHEMA,
    examples=[PARTNER_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Mangal Dosha status for both partners',
            response={
                'type': 'object',
                'properties': {
                    'status':               {'type': 'string',  'example': 'success'},
                    'double_dosha_cancels': {'type': 'boolean', 'example': False},
                    'note':                 {'type': 'string',  'example': 'Check individual dosha details above.'},
                    'boy': {
                        'type': 'object',
                        'properties': {
                            'has_mangal_dosha':  {'type': 'boolean', 'example': False},
                            'mars_house_lagna':  {'type': 'integer', 'example': 10},
                            'mars_house_moon':   {'type': 'integer', 'example': 7},
                            'mars_house_venus':  {'type': 'integer', 'example': 2},
                            'severity':          {'type': 'string',  'example': 'None'},
                            'cancellations':     {'type': 'array', 'items': {'type': 'string'}},
                            'mars_rasi':         {'type': 'string',  'example': 'Aries'},
                            'ascendant_rasi':    {'type': 'string',  'example': 'Cancer'},
                        },
                    },
                    'girl': {'type': 'object', 'description': 'Same structure as boy'},
                },
            },
        ),
        400: OpenApiResponse(description='Missing boy/girl data or validation error'),
    },
)
@api_view(['POST'])
@throttle_classes([CompatibilityThrottle])
def mangal_dosha(request):
    boy_data  = request.data.get('boy')
    girl_data = request.data.get('girl')

    if not boy_data or not girl_data:
        return Response(
            {'errors': 'Both "boy" and "girl" birth data are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    boy_serializer  = BirthDataSerializer(data=boy_data)
    girl_serializer = BirthDataSerializer(data=girl_data)

    errors = {}
    if not boy_serializer.is_valid():
        errors['boy'] = boy_serializer.errors
    if not girl_serializer.is_valid():
        errors['girl'] = girl_serializer.errors
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    b = boy_serializer.validated_data
    g = girl_serializer.validated_data

    jd_boy  = get_julian_day(b['year'], b['month'], b['day'],
                              int(b['hour'] - b['utc_offset']), b['minute'])
    jd_girl = get_julian_day(g['year'], g['month'], g['day'],
                              int(g['hour'] - g['utc_offset']), g['minute'])

    boy_dosha  = check_mangal_dosha(jd_boy,  b['latitude'], b['longitude'])
    girl_dosha = check_mangal_dosha(jd_girl, g['latitude'], g['longitude'])

    double_dosha_cancels = (
        boy_dosha['has_mangal_dosha'] and girl_dosha['has_mangal_dosha']
    )

    return Response({
        'status':               'success',
        'boy':                  boy_dosha,
        'girl':                 girl_dosha,
        'double_dosha_cancels': double_dosha_cancels,
        'note': (
            "Both partners have Mangal Dosha — cancels each other in most traditions."
            if double_dosha_cancels else
            "Check individual dosha details above."
        ),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — TRANSITS (GOCHAR)
# ═══════════════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['Transits'],
    summary='Current planetary transits vs natal chart',
    description=(
        'Shows where **all planets are right now** compared to your natal chart.\n\n'
        'For each transiting planet returns:\n'
        '- Which natal house it currently occupies\n'
        '- Classical effect for that house placement\n'
        '- Ashtakavarga score for the transiting sign (higher = better)\n'
        '- Retrograde status\n'
        '- Conjunctions with natal planets (within 3° orb)\n'
        '- Overall favorability flag\n\n'
        'Also includes **Sade Sati / Dhaiya check** and detailed **Moon transit** data.\n\n'
        'Send your **natal birth data** — the transit time is always the current UTC moment.'
    ),
    request=BIRTH_REQUEST_SCHEMA,
    examples=[KATHMANDU_EXAMPLE],
    responses={
        200: OpenApiResponse(
            description='Current transits with Sade Sati and Moon transit details',
            response={
                'type': 'object',
                'properties': {
                    'status':       {'type': 'string', 'example': 'success'},
                    'transit_time': {'type': 'string', 'example': '2026-03-15 04:30 UTC'},
                    'ayanamsa':     {'type': 'string', 'example': 'Lahiri'},
                    'sade_sati': {
                        'type': 'object',
                        'properties': {
                            'in_sade_sati':       {'type': 'boolean', 'example': False},
                            'sade_sati_phase':    {'type': 'string',  'example': None},
                            'in_dhaiya':          {'type': 'boolean', 'example': False},
                            'natal_moon_rasi':    {'type': 'string',  'example': 'Libra'},
                            'transit_saturn_rasi':{'type': 'string',  'example': 'Pisces'},
                        },
                    },
                    'moon_transit': {
                        'type': 'object',
                        'properties': {
                            'rasi':                  {'type': 'string',  'example': 'Capricorn'},
                            'nakshatra':             {'type': 'string',  'example': 'Uttara Ashadha'},
                            'pada':                  {'type': 'integer', 'example': 3},
                            'hours_to_next_sign':    {'type': 'number',  'example': 46.8},
                            'next_rasi':             {'type': 'string',  'example': 'Aquarius'},
                        },
                    },
                    'transits': {
                        'type': 'array',
                        'description': 'Sorted by planet importance (Jupiter first)',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'planet':        {'type': 'string',  'example': 'jupiter'},
                                'transit_rasi':  {'type': 'string',  'example': 'Gemini'},
                                'transit_house': {'type': 'integer', 'example': 12},
                                'retrograde':    {'type': 'boolean', 'example': False},
                                'avarga_score':  {'type': 'integer', 'example': 6},
                                'favorable':     {'type': 'boolean', 'example': True},
                                'effect':        {'type': 'string',  'example': 'Spiritual growth, foreign travel, moksha themes'},
                                'conjunctions':  {'type': 'array',   'items': {'type': 'object'}},
                            },
                        },
                    },
                },
            },
        ),
        400: ERROR_400,
    },
)
@api_view(['POST'])
@throttle_classes([TransitThrottle])
def transits_current(request):
    d, jd_natal, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    jd_now   = get_current_jd()
    now_utc  = __import__('datetime').datetime.utcnow()

    transits  = analyze_transits(jd_natal, jd_now, d['latitude'], d['longitude'])
    sade_sati = get_sade_sati(jd_natal, jd_now)
    moon_now  = get_moon_transit(jd_now)

    return Response({
        'status':       'success',
        'transit_time': str(now_utc.strftime('%Y-%m-%d %H:%M UTC')),
        'ayanamsa':     'Lahiri',
        'sade_sati':    sade_sati,
        'moon_transit': moon_now,
        'transits':     transits,
    })


@extend_schema(
    tags=['Transits'],
    summary='Transits for a specific date vs natal chart',
    description=(
        'Same as `/transits/current/` but for **any date you specify**.\n\n'
        'Useful for:\n'
        '- Future planning (checking transits for an upcoming event date)\n'
        '- Past analysis (what was happening during a specific period)\n'
        '- Muhurta (auspicious timing) research\n\n'
        'Pass natal birth data **plus** `transit_year`, `transit_month`, `transit_day` '
        '(and optionally `transit_hour`, `transit_minute`).'
    ),
    request={
        'application/json': {
            'type': 'object',
            'required': [*BIRTH_DATA_REQUIRED, 'transit_year', 'transit_month', 'transit_day'],
            'properties': {
                **BIRTH_DATA_PROPERTIES,
                'transit_year':   {'type': 'integer', 'example': 2026, 'description': 'Year of transit date'},
                'transit_month':  {'type': 'integer', 'example': 6,    'description': 'Month of transit date (1–12)'},
                'transit_day':    {'type': 'integer', 'example': 15,   'description': 'Day of transit date'},
                'transit_hour':   {'type': 'integer', 'example': 12,   'description': 'Hour of transit (default: 12)'},
                'transit_minute': {'type': 'integer', 'example': 0,    'description': 'Minute of transit (default: 0)'},
            },
        }
    },
    examples=[
        OpenApiExample('Transits for June 15 2026', value={
            'year': 1998, 'month': 5, 'day': 10,
            'hour': 10, 'minute': 30,
            'latitude': 27.7172, 'longitude': 85.3240,
            'utc_offset': 5.75, 'house_system': 'whole_sign',
            'transit_year': 2026, 'transit_month': 6, 'transit_day': 15,
            'transit_hour': 12,   'transit_minute': 0,
        }, request_only=True),
    ],
    responses={
        200: OpenApiResponse(description='Transits for the specified date vs natal chart'),
        400: OpenApiResponse(description='Missing transit_year/month/day or birth data validation error'),
    },
)
@api_view(['POST'])
@throttle_classes([TransitThrottle])
def transits_date(request):
    d, jd_natal, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        t_year   = int(request.data['transit_year'])
        t_month  = int(request.data['transit_month'])
        t_day    = int(request.data['transit_day'])
        t_hour   = int(request.data.get('transit_hour', 12))
        t_minute = int(request.data.get('transit_minute', 0))
    except (KeyError, ValueError, TypeError):
        return Response(
            {'errors': 'transit_year, transit_month, transit_day are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    jd_transit = get_julian_day(t_year, t_month, t_day, t_hour, t_minute)

    transits  = analyze_transits(jd_natal, jd_transit, d['latitude'], d['longitude'])
    sade_sati = get_sade_sati(jd_natal, jd_transit)
    moon_data = get_moon_transit(jd_transit)

    return Response({
        'status':       'success',
        'transit_date': f'{t_year}-{t_month:02d}-{t_day:02d}',
        'ayanamsa':     'Lahiri',
        'sade_sati':    sade_sati,
        'moon_transit': moon_data,
        'transits':     transits,
    })


@extend_schema(
    tags=['Transits'],
    summary='Moon transit — Chandra Gochar',
    description=(
        '**Chandra Gochar** — detailed Moon transit information.\n\n'
        'The Moon changes sign every ~2.25 days and nakshatra every ~1 day, making this '
        'the most frequently changing transit and a key feature for daily horoscope apps.\n\n'
        'Returns:\n'
        '- Current rasi (zodiac sign) and degree within it\n'
        '- Current nakshatra, lord, and pada\n'
        '- Moon speed (degrees/day)\n'
        '- Degrees and hours remaining until the next sign change\n'
        '- Next sign name\n\n'
        '**No birth data required.** Defaults to the current moment. '
        'Optionally pass `transit_year`, `transit_month`, `transit_day` for a specific date.'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'transit_year':   {'type': 'integer', 'example': 2026, 'description': 'Optional. Defaults to today.'},
                'transit_month':  {'type': 'integer', 'example': 3},
                'transit_day':    {'type': 'integer', 'example': 15},
                'transit_hour':   {'type': 'integer', 'example': 12},
                'transit_minute': {'type': 'integer', 'example': 0},
            },
        }
    },
    examples=[
        OpenApiExample('Current Moon transit (empty body)', value={}, request_only=True),
        OpenApiExample('Moon on specific date', value={
            'transit_year': 2026, 'transit_month': 6, 'transit_day': 15,
        }, request_only=True),
    ],
    responses={
        200: OpenApiResponse(
            description='Detailed Moon transit data',
            response={
                'type': 'object',
                'properties': {
                    'status':                 {'type': 'string',  'example': 'success'},
                    'ayanamsa':               {'type': 'string',  'example': 'Lahiri'},
                    'moon_longitude':         {'type': 'number',  'example': 284.3821},
                    'rasi':                   {'type': 'string',  'example': 'Capricorn'},
                    'rasi_index':             {'type': 'integer', 'example': 9},
                    'degree_in_rasi':         {'type': 'number',  'example': 14.3821},
                    'nakshatra':              {'type': 'string',  'example': 'Uttara Ashadha'},
                    'nakshatra_lord':         {'type': 'string',  'example': 'Sun'},
                    'pada':                   {'type': 'integer', 'example': 3},
                    'speed_deg_per_day':      {'type': 'number',  'example': 13.2541},
                    'degrees_to_next_sign':   {'type': 'number',  'example': 15.6179},
                    'hours_to_next_sign':     {'type': 'number',  'example': 28.3},
                    'next_rasi':              {'type': 'string',  'example': 'Aquarius'},
                },
            },
        ),
        400: OpenApiResponse(description='Invalid transit date format'),
    },
)
@api_view(['POST'])
def transits_moon(request):
    transit_year  = request.data.get('transit_year')
    transit_month = request.data.get('transit_month')
    transit_day   = request.data.get('transit_day')

    if transit_year and transit_month and transit_day:
        try:
            jd_transit = get_julian_day(
                int(transit_year), int(transit_month), int(transit_day),
                int(request.data.get('transit_hour', 12)),
                int(request.data.get('transit_minute', 0)),
            )
        except (ValueError, TypeError):
            return Response(
                {'errors': 'Invalid transit date provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        jd_transit = get_current_jd()

    moon_data = get_moon_transit(jd_transit)

    return Response({'status': 'success', 'ayanamsa': 'Lahiri', **moon_data})