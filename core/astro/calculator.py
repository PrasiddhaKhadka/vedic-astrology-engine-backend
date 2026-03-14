import swisseph as swe
from django.conf import settings
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora import const

# Planet constants mapped to readable names
PLANETS = {
    'sun':     swe.SUN,
    'moon':    swe.MOON,
    'mars':    swe.MARS,
    'mercury': swe.MERCURY,
    'jupiter': swe.JUPITER,
    'venus':   swe.VENUS,
    'saturn':  swe.SATURN,
    'rahu':    swe.MEAN_NODE,   # North Node
}

# Rahu/Ketu are always 180° apart
RASI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

HOUSE_SYSTEMS = {
    'placidus':    b'P',
    'whole_sign':  b'W',
    'equal':       b'E',
    'koch':        b'K',
}


def init_ephe():
    """Initialize Swiss Ephemeris with the ephemeris path."""
    swe.set_ephe_path(str(settings.EPHE_PATH))
    # Use Lahiri ayanamsa (standard for Vedic/Jyotish)
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def get_julian_day(year, month, day, hour, minute, second=0):
    """Convert datetime to Julian Day Number."""
    decimal_hour = hour + minute / 60.0 + second / 3600.0
    return swe.julday(year, month, day, decimal_hour)


def longitude_to_rasi(longitude):
    """Convert ecliptic longitude to rasi (sign) name and degree within sign."""
    rasi_index = int(longitude / 30)
    degree_in_rasi = longitude % 30
    return {
        'rasi': RASI_NAMES[rasi_index],
        'rasi_index': rasi_index,           # 0 = Aries, 11 = Pisces
        'degree_in_rasi': round(degree_in_rasi, 4),
    }


def get_planet_positions(jd):
    """
    Calculate sidereal (Vedic) positions for all planets.
    Returns a dict of planet_name → position data.
    """
    init_ephe()
    positions = {}

    for name, planet_id in PLANETS.items():
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        result, ret_flag = swe.calc_ut(jd, planet_id, flags)

        longitude = result[0]
        latitude  = result[1]
        speed     = result[3]   # deg/day — negative = retrograde

        rasi_data = longitude_to_rasi(longitude)

        positions[name] = {
            'longitude': round(longitude, 6),
            'latitude':  round(latitude, 6),
            'speed':     round(speed, 6),
            'retrograde': speed < 0,
            **rasi_data,
        }

    # Ketu = Rahu + 180°
    rahu_long = positions['rahu']['longitude']
    ketu_long = (rahu_long + 180.0) % 360.0
    positions['ketu'] = {
        'longitude': round(ketu_long, 6),
        'latitude':  0.0,
        'speed':     positions['rahu']['speed'],
        'retrograde': True,  # Ketu is always considered retrograde
        **longitude_to_rasi(ketu_long),
    }

    return positions


def get_ascendant_and_houses(jd, latitude, longitude, house_system='whole_sign'):
    """
    Calculate Ascendant (Lagna) and 12 house cusps.
    Uses sidereal (Vedic) calculation with Lahiri ayanamsa.
    """
    init_ephe()

    hsys = HOUSE_SYSTEMS.get(house_system, b'W')

    # swe.houses_ex returns (cusps, ascmc) with sidereal flag
    cusps, ascmc = swe.houses_ex(
        jd,
        latitude,
        longitude,
        hsys,
        swe.FLG_SIDEREAL
    )

    ascendant_long = ascmc[0]
    mc_long        = ascmc[1]   # Midheaven
    armc           = ascmc[2]   # ARMC
    vertex         = ascmc[3]

    houses = []
    for i, cusp in enumerate(cusps, start=1):   # cusps[0] is unused
        rasi_data = longitude_to_rasi(cusp % 360)
        houses.append({
            'house': i,
            'cusp_longitude': round(cusp % 360, 6),
            **rasi_data,
        })

    return {
        'ascendant': {
            'longitude': round(ascendant_long, 6),
            **longitude_to_rasi(ascendant_long),
        },
        'midheaven': {
            'longitude': round(mc_long, 6),
            **longitude_to_rasi(mc_long),
        },
        'houses': houses,
        'house_system': house_system,
    }

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

YOGA_NAMES = [
    "Vishkambha", "Preeti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

# Vimshottari Dasha sequence and years
DASHA_SEQUENCE = [
    ("Ketu",    7),
    ("Venus",  20),
    ("Sun",     6),
    ("Moon",   10),
    ("Mars",    7),
    ("Rahu",   18),
    ("Jupiter",16),
    ("Saturn", 19),
    ("Mercury",17),
]

TOTAL_DASHA_YEARS = 120


def get_moon_longitude(jd):
    """Get sidereal Moon longitude for a given JD."""
    init_ephe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result, _ = swe.calc_ut(jd, swe.MOON, flags)
    return result[0]


def get_nakshatra(jd):
    """
    Calculate Nakshatra, Pada, lord and deity from Moon longitude.
    Each nakshatra = 13°20' (13.333°). Each pada = 3°20' (3.333°).
    """
    moon_long = get_moon_longitude(jd)

    nakshatra_index = int(moon_long / (360 / 27))   # 0–26
    degree_in_nak   = moon_long % (360 / 27)
    pada            = int(degree_in_nak / (360 / 108)) + 1  # 1–4

    name = NAKSHATRA_NAMES[nakshatra_index]
    lord = NAKSHATRA_LORDS[nakshatra_index]

    return {
        'nakshatra':        name,
        'nakshatra_index':  nakshatra_index + 1,   # 1-based
        'pada':             pada,
        'lord':             lord,
        'moon_longitude':   round(moon_long, 6),
        'degree_in_nakshatra': round(degree_in_nak, 4),
    }


def get_sun_longitude(jd):
    """Get sidereal Sun longitude for a given JD."""
    init_ephe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result, _ = swe.calc_ut(jd, swe.SUN, flags)
    return result[0]


def get_panchang(jd, latitude, longitude):
    """
    Calculate the 5 elements of Panchang:
    Tithi, Vara, Nakshatra, Yoga, Karana
    """
    moon_long = get_moon_longitude(jd)
    sun_long  = get_sun_longitude(jd)

    # Tithi — each tithi = 12° difference between Moon and Sun
    tithi_angle = (moon_long - sun_long) % 360
    tithi_index = int(tithi_angle / 12)          # 0–29
    tithi_name  = TITHI_NAMES[tithi_index % 15]
    paksha      = "Shukla" if tithi_index < 15 else "Krishna"

    # Vara — weekday from Julian Day
    vara_index = int(jd + 1.5) % 7
    vara_name  = VARA_NAMES[vara_index]

    # Nakshatra
    nakshatra_data = get_nakshatra(jd)

    # Yoga — (Sun longitude + Moon longitude) / 13.333°
    yoga_angle = (sun_long + moon_long) % 360
    yoga_index = int(yoga_angle / (360 / 27))
    yoga_name  = YOGA_NAMES[yoga_index]

    # Karana — half of a tithi (6° difference)
    karana_index = int(tithi_angle / 6) % 11
    karana_name  = KARANA_NAMES[karana_index]

    return {
        'tithi': {
            'name':   tithi_name,
            'paksha': paksha,
            'index':  tithi_index + 1,
        },
        'vara': {
            'name':  vara_name,
            'index': vara_index,
        },
        'nakshatra': nakshatra_data,
        'yoga': {
            'name':  yoga_name,
            'index': yoga_index + 1,
        },
        'karana': {
            'name':  karana_name,
            'index': karana_index + 1,
        },
    }


def get_vimshottari_dasha(jd):
    """
    Calculate Vimshottari Dasha periods from Moon's Nakshatra.

    Algorithm:
    1. Find Moon nakshatra → determines starting dasha lord
    2. Find how much of that dasha is already elapsed
    3. Generate all mahadashas for 120 years from birth
    """
    moon_long = get_moon_longitude(jd)

    nak_index       = int(moon_long / (360 / 27))       # 0–26
    degree_in_nak   = moon_long % (360 / 27)            # 0–13.333°
    nak_span        = 360 / 27                          # 13.333°

    # Fraction of nakshatra already traversed
    fraction_elapsed = degree_in_nak / nak_span

    # Starting dasha lord index in DASHA_SEQUENCE
    start_lord_index = nak_index % 9

    # Years elapsed in starting dasha
    start_dasha_years   = DASHA_SEQUENCE[start_lord_index][1]
    years_elapsed       = fraction_elapsed * start_dasha_years
    years_remaining     = start_dasha_years - years_elapsed

    # Build Mahadasha list from birth
    import datetime
    birth_dt = swe.revjul(jd)   # (year, month, day, hour_float)
    birth_date = datetime.date(int(birth_dt[0]), int(birth_dt[1]), int(birth_dt[2]))

    dashas = []
    current_date = birth_date

    for i in range(9):
        lord_index  = (start_lord_index + i) % 9
        lord_name   = DASHA_SEQUENCE[lord_index][0]
        dasha_years = DASHA_SEQUENCE[lord_index][1]

        if i == 0:
            # First dasha: only remaining portion
            duration_years = years_remaining
        else:
            duration_years = dasha_years

        duration_days = int(duration_years * 365.25)
        end_date      = current_date + datetime.timedelta(days=duration_days)

        dashas.append({
            'lord':       lord_name,
            'start_date': str(current_date),
            'end_date':   str(end_date),
            'years':      round(duration_years, 4),
        })

        current_date = end_date

    return {
        'system':       'Vimshottari',
        'total_years':  TOTAL_DASHA_YEARS,
        'moon_nakshatra': NAKSHATRA_NAMES[nak_index],
        'mahadasha':    dashas,
    }