from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import BirthDataSerializer
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
)


def parse_birth_data(request):
    """
    Helper: validate request, return (serializer_data, julian_day) or raise.
    Adjusts input time to UTC using utc_offset.
    """
    serializer = BirthDataSerializer(data=request.data)
    if not serializer.is_valid():
        return None, None, serializer.errors

    d = serializer.validated_data

    # Convert local birth time → UTC
    utc_hour   = d['hour'] - d['utc_offset']
    utc_minute = d['minute']

    # Handle day rollover (e.g. birth at 01:00 IST = 19:30 UTC previous day)
    day   = d['day']
    month = d['month']
    year  = d['year']

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


@api_view(['POST'])
def planet_positions(request):
    """
    POST /api/v1/planets/

    Returns sidereal (Vedic/Lahiri) positions of all 9 Jyotish grahas.

    Body:
        year, month, day, hour, minute  — birth datetime (local time)
        latitude, longitude             — birth location
        utc_offset                      — e.g. 5.75 for Nepal (NPT)
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    positions = get_planet_positions(jd)

    return Response({
        'status': 'success',
        'ayanamsa': 'Lahiri',
        'system': 'Vedic (Sidereal)',
        'planets': positions,
    })


@api_view(['POST'])
def ascendant_houses(request):
    """
    POST /api/v1/houses/

    Returns Ascendant (Lagna) and 12 house cusps.

    Body:
        year, month, day, hour, minute  — birth datetime (local time)
        latitude, longitude             — birth location
        utc_offset                      — e.g. 5.75 for Nepal (NPT)
        house_system                    — whole_sign (default), placidus, equal, koch
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_ascendant_and_houses(
        jd,
        d['latitude'],
        d['longitude'],
        d['house_system']
    )

    return Response({
        'status': 'success',
        'ayanamsa': 'Lahiri',
        'system': 'Vedic (Sidereal)',
        **result,
    })


@api_view(['POST'])
def full_chart(request):
    """
    POST /api/v1/chart/

    Combined endpoint — returns both planet positions AND houses in one call.
    This is the most commonly used endpoint for chart rendering.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    planets = get_planet_positions(jd)
    houses  = get_ascendant_and_houses(
        jd,
        d['latitude'],
        d['longitude'],
        d['house_system']
    )

    return Response({
        'status': 'success',
        'ayanamsa': 'Lahiri',
        'system': 'Vedic (Sidereal)',
        'planets': planets,
        **houses,
    })

@api_view(['POST'])
def nakshatra(request):
    """
    POST /api/v1/nakshatra/

    Returns Moon's Nakshatra, Pada, and lord.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_nakshatra(jd)

    return Response({
        'status':   'success',
        'ayanamsa': 'Lahiri',
        **result,
    })


@api_view(['POST'])
def panchang(request):
    """
    POST /api/v1/panchang/

    Returns the 5 Panchang elements:
    Tithi, Vara (weekday), Nakshatra, Yoga, Karana.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_panchang(jd, d['latitude'], d['longitude'])

    return Response({
        'status':   'success',
        'ayanamsa': 'Lahiri',
        **result,
    })


@api_view(['POST'])
def dasha(request):
    """
    POST /api/v1/dasha/

    Returns Vimshottari Mahadasha periods for 120 years from birth.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_vimshottari_dasha(jd)

    return Response({
        'status': 'success',
        **result,
    })


@api_view(['POST'])
def antardasha(request):
    """
    POST /api/v1/antardasha/

    Returns Vimshottari Mahadasha with full Antardasha (sub-periods)
    nested inside each Mahadasha period.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_antardasha(jd)

    return Response({
        'status': 'success',
        **result,
    })


@api_view(['POST'])
def divisional_chart(request):
    """
    POST /api/v1/divisional/

    Returns a divisional chart for a given division number.

    Pass 'division' in the request body:
        9  = D9 Navamsa  (spouse, dharma)
        10 = D10 Dashamsa (career)
        2  = D2 Hora
        3  = D3 Drekkana
        12 = D12 Dwadashamsa
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    division = request.data.get('division', 9)
    try:
        division = int(division)
        if division not in [2, 3, 9, 10, 12]:
            raise ValueError
    except (ValueError, TypeError):
        return Response(
            {'errors': {'division': 'Must be one of: 2, 3, 9, 10, 12'}},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = get_divisional_chart(jd, division)

    return Response({
        'status':   'success',
        'ayanamsa': 'Lahiri',
        **result,
    })


@api_view(['POST'])
def yogas(request):
    """
    POST /api/v1/yogas/

    Detects major Vedic Yogas present in the birth chart:
    - Pancha Mahapurusha Yogas
    - Gajakesari, Budha-Aditya, Chandra-Mangala
    - Dhana Yoga
    - Kemadruma Yoga
    - Neecha Bhanga Raja Yoga
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_yogas(jd, d['latitude'], d['longitude'])

    return Response({
        'status':   'success',
        'ayanamsa': 'Lahiri',
        **result,
    })


@api_view(['POST'])
def ashtakavarga(request):
    """
    POST /api/v1/ashtakavarga/

    Returns Ashtakavarga scores for each planet across all 12 signs,
    plus the combined Sarvashtakavarga totals.

    Higher scores = stronger transit/placement in that sign.
    Score >= 5 = Strong, 3-4 = Moderate, < 3 = Weak.
    Sarva >= 30 = Strong sign, 25-29 = Moderate, < 25 = Weak.
    """
    d, jd, errors = parse_birth_data(request)
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    result = get_ashtakavarga(jd, d['latitude'], d['longitude'])

    return Response({
        'status':   'success',
        'ayanamsa': 'Lahiri',
        **result,
    })