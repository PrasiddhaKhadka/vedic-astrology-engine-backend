import swisseph as swe
from django.conf import settings
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora import const
import datetime as dt


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



def get_antardasha(jd):
    """
    Calculate Vimshottari Antardasha (sub-periods) for each Mahadasha.

    Formula for antardasha duration:
    Antardasha of planet B inside Mahadasha of planet A =
        (years_of_A * years_of_B) / 120 years
    """
    import datetime

    moon_long       = get_moon_longitude(jd)
    nak_index       = int(moon_long / (360 / 27))
    degree_in_nak   = moon_long % (360 / 27)
    nak_span        = 360 / 27
    fraction_elapsed = degree_in_nak / nak_span

    start_lord_index    = nak_index % 9
    start_dasha_years   = DASHA_SEQUENCE[start_lord_index][1]
    years_remaining     = start_dasha_years * (1 - fraction_elapsed)

    birth_dt   = swe.revjul(jd)
    birth_date = datetime.date(int(birth_dt[0]), int(birth_dt[1]), int(birth_dt[2]))

    mahadashas = []
    maha_start = birth_date

    for i in range(9):
        maha_index  = (start_lord_index + i) % 9
        maha_lord   = DASHA_SEQUENCE[maha_index][0]
        maha_years  = DASHA_SEQUENCE[maha_index][1]
        maha_duration = years_remaining if i == 0 else maha_years

        # Antardashas start from the mahadasha lord itself
        antardashas = []
        antar_start = maha_start

        for j in range(9):
            antar_index = (maha_index + j) % 9
            antar_lord  = DASHA_SEQUENCE[antar_index][0]
            antar_years = DASHA_SEQUENCE[antar_index][1]

            # Antardasha duration = (maha_years * antar_years) / 120
            # But for first mahadasha, scale proportionally
            if i == 0:
                antar_duration = (maha_duration / maha_years) * (maha_years * antar_years / TOTAL_DASHA_YEARS)
            else:
                antar_duration = (maha_years * antar_years) / TOTAL_DASHA_YEARS

            antar_days = int(antar_duration * 365.25)
            antar_end  = antar_start + datetime.timedelta(days=antar_days)

            antardashas.append({
                'lord':       antar_lord,
                'start_date': str(antar_start),
                'end_date':   str(antar_end),
                'years':      round(antar_duration, 4),
            })
            antar_start = antar_end

        maha_end = antar_start  # end of last antardasha = end of mahadasha

        mahadashas.append({
            'lord':        maha_lord,
            'start_date':  str(maha_start),
            'end_date':    str(maha_end),
            'years':       round(maha_duration, 4),
            'antardasha':  antardashas,
        })
        maha_start = maha_end

    return {
        'system':         'Vimshottari',
        'moon_nakshatra': NAKSHATRA_NAMES[nak_index],
        'mahadasha':      mahadashas,
    }


# ─── DIVISIONAL CHARTS ─────────────────────────────────────────────

RASI_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]


def get_divisional_chart(jd, division):
    """
    Calculate divisional chart positions for all planets.

    Supported divisions:
    D2  = Hora             — wealth
    D3  = Drekkana         — siblings, courage
    D7  = Saptamsa         — children, progeny
    D9  = Navamsa          — spouse, dharma, inner self (most important)
    D10 = Dashamsa         — career, profession
    D12 = Dwadashamsa      — parents
    D16 = Shodashamsa      — vehicles, comforts, happiness
    D30 = Trimshamsa       — misfortunes, health, evil deeds
    D60 = Shashtiamsa      — most detailed karma chart
    """
    init_ephe()

    planet_positions = get_planet_positions(jd)
    div_positions    = {}

    def calc_div_rasi(rasi_index, deg_in_rasi, division):
        """
        Core divisional chart calculation.
        Returns the divisional rasi index (0-11).
        """
        part_size  = 30.0 / division
        part_num   = int(deg_in_rasi / part_size)   # 0-based

        # ── D2 Hora ────────────────────────────────────────────────
        # Odd signs (Aries etc): 1st half=Leo, 2nd half=Cancer
        # Even signs: 1st half=Cancer, 2nd half=Leo
        if division == 2:
            if rasi_index % 2 == 0:   # odd sign
                return 4 if part_num == 0 else 3   # Leo or Cancer
            else:                      # even sign
                return 3 if part_num == 0 else 4

        # ── D3 Drekkana ─────────────────────────────────────────────
        # 1st decan = same sign
        # 2nd decan = 5th from sign
        # 3rd decan = 9th from sign
        elif division == 3:
            offsets = [0, 4, 8]
            return (rasi_index + offsets[part_num]) % 12

        # ── D7 Saptamsa ─────────────────────────────────────────────
        # Odd signs: count from same sign
        # Even signs: count from 7th sign
        elif division == 7:
            if rasi_index % 2 == 0:   # odd sign
                return (rasi_index + part_num) % 12
            else:                      # even sign
                return (rasi_index + 6 + part_num) % 12

        # ── D9 Navamsa ──────────────────────────────────────────────
        # Fire signs  (0,4,8):  start from Aries   (0)
        # Earth signs (1,5,9):  start from Capricorn(9)
        # Air signs   (2,6,10): start from Libra    (6)
        # Water signs (3,7,11): start from Cancer   (3)
        elif division == 9:
            element    = rasi_index % 4
            start_map  = {0: 0, 1: 9, 2: 6, 3: 3}
            start_sign = start_map[element]
            return (start_sign + part_num) % 12

        # ── D10 Dashamsa ────────────────────────────────────────────
        # Odd signs:  count from same sign
        # Even signs: count from 9th sign
        elif division == 10:
            if rasi_index % 2 == 0:   # odd sign
                return (rasi_index + part_num) % 12
            else:                      # even sign
                return (rasi_index + 8 + part_num) % 12

        # ── D12 Dwadashamsa ─────────────────────────────────────────
        # Always count from same sign
        elif division == 12:
            return (rasi_index + part_num) % 12

        # ── D16 Shodashamsa ─────────────────────────────────────────
        # Movable signs  (0,3,6,9):  start from Aries  (0)
        # Fixed signs    (1,4,7,10): start from Leo     (4)
        # Mutable signs  (2,5,8,11): start from Sagittarius (8)
        elif division == 16:
            modality   = rasi_index % 3
            start_map  = {0: 0, 1: 4, 2: 8}
            start_sign = start_map[modality]
            return (start_sign + part_num) % 12

        # ── D30 Trimshamsa ──────────────────────────────────────────
        # Special unequal division — classical Parashari rules:
        # Odd signs:
        #   Mars  : 0–5°
        #   Saturn: 5–10°
        #   Jupiter: 10–18°
        #   Mercury: 18–25°
        #   Venus  : 25–30°
        # Even signs: reverse order
        # Trimshamsa lords map to their own signs
        elif division == 30:
            ODD_TRIMSHA = [
                (5,  0),   # Mars    → Aries  (0)
                (10, 9),   # Saturn  → Capricorn (9)
                (18, 8),   # Jupiter → Sagittarius (8)
                (25, 2),   # Mercury → Gemini (2)
                (30, 6),   # Venus   → Libra  (6)
            ]
            EVEN_TRIMSHA = [
                (5,  6),   # Venus   → Libra
                (12, 2),   # Mercury → Gemini
                (20, 8),   # Jupiter → Sagittarius
                (25, 9),   # Saturn  → Capricorn
                (30, 0),   # Mars    → Aries
            ]
            table = ODD_TRIMSHA if rasi_index % 2 == 0 else EVEN_TRIMSHA
            for threshold, result_sign in table:
                if deg_in_rasi < threshold:
                    return result_sign
            return table[-1][1]

        # ── D60 Shashtiamsa ─────────────────────────────────────────
        # Each sign divided into 60 parts of 0.5° each.
        # Count from same sign cyclically through all 12.
        elif division == 60:
            return (rasi_index + part_num) % 12

        # Fallback
        else:
            return rasi_index

    # Calculate for each planet
    for planet_name, data in planet_positions.items():
        longitude   = data['longitude']
        rasi_index  = data['rasi_index']
        deg_in_rasi = data['degree_in_rasi']

        div_rasi_index = calc_div_rasi(rasi_index, deg_in_rasi, division)
        div_rasi       = RASI_NAMES[div_rasi_index]
        div_lord       = RASI_LORDS[div_rasi_index]

        div_positions[planet_name] = {
            'rasi':               div_rasi,
            'rasi_index':         div_rasi_index,
            'lord':               div_lord,
            'original_longitude': round(longitude, 6),
            'original_rasi':      data['rasi'],
            'degree_in_rasi':     round(deg_in_rasi, 4),
        }

    # Ascendant in divisional chart
    asc_data    = get_ascendant_and_houses(jd, 0, 0)
    asc_long    = asc_data['ascendant']['longitude']
    asc_rasi    = int(asc_long / 30)
    asc_deg     = asc_long % 30

    div_asc_index = calc_div_rasi(asc_rasi, asc_deg, division)

    # Division metadata
    DIVISION_INFO = {
        2:  {'name': 'Hora',           'purpose': 'Wealth and finances'},
        3:  {'name': 'Drekkana',        'purpose': 'Siblings and courage'},
        7:  {'name': 'Saptamsa',        'purpose': 'Children and progeny'},
        9:  {'name': 'Navamsa',         'purpose': 'Spouse, dharma, inner self'},
        10: {'name': 'Dashamsa',        'purpose': 'Career and profession'},
        12: {'name': 'Dwadashamsa',     'purpose': 'Parents and ancestors'},
        16: {'name': 'Shodashamsa',     'purpose': 'Vehicles and comforts'},
        30: {'name': 'Trimshamsa',      'purpose': 'Misfortunes and health challenges'},
        60: {'name': 'Shashtiamsa',     'purpose': 'Detailed karma, most sensitive chart'},
    }

    info = DIVISION_INFO.get(division, {'name': f'D{division}', 'purpose': ''})

    return {
        'division':   division,
        'chart_name': info['name'],
        'purpose':    info['purpose'],
        'ascendant':  {
            'rasi':       RASI_NAMES[div_asc_index],
            'rasi_index': div_asc_index,
            'lord':       RASI_LORDS[div_asc_index],
        },
        'planets': div_positions,
    }

# ─── YOGAS ─────────────────────────────────────────────────────────

def get_yogas(jd, latitude, longitude):
    """
    Detect major Vedic Yogas from planet positions.

    Checks for:
    - Raj Yogas (planets in kendra + trikona relationship)
    - Dhana Yogas (wealth combinations)
    - Pancha Mahapurusha Yogas (planets in own/exalted sign in kendra)
    - Gajakesari Yoga (Jupiter-Moon relationship)
    - Budha-Aditya Yoga (Sun-Mercury conjunction)
    - Chandra-Mangala Yoga (Moon-Mars conjunction/mutual aspect)
    - Kemadruma Yoga (Moon alone)
    - Neecha Bhanga Raja Yoga
    """
    planets = get_planet_positions(jd)
    houses  = get_ascendant_and_houses(jd, latitude, longitude)

    asc_rasi = houses['ascendant']['rasi_index']

    # Map each planet to its house number (1–12)
    def planet_house(planet_rasi_index):
        return ((planet_rasi_index - asc_rasi) % 12) + 1

    # Kendra houses: 1, 4, 7, 10
    KENDRA = {1, 4, 7, 10}
    # Trikona houses: 1, 5, 9
    TRIKONA = {1, 5, 9}
    # Dusthana houses: 6, 8, 12
    DUSTHANA = {6, 8, 12}

    # Exaltation signs
    EXALTATION = {
        'sun': 0, 'moon': 1, 'mars': 9, 'mercury': 5,
        'jupiter': 3, 'venus': 11, 'saturn': 6
    }
    # Own signs
    OWN_SIGN = {
        'sun':     [4],
        'moon':    [3],
        'mars':    [0, 7],
        'mercury': [2, 5],
        'jupiter': [8, 11],
        'venus':   [1, 6],
        'saturn':  [9, 10],
    }
    # Debilitation signs
    DEBILITATION = {
        'sun': 6, 'moon': 7, 'mars': 3, 'mercury': 11,
        'jupiter': 9, 'venus': 5, 'saturn': 0
    }

    yogas_found = []

    sun_rasi  = planets['sun']['rasi_index']
    moon_rasi = planets['moon']['rasi_index']
    mars_rasi = planets['mars']['rasi_index']
    merc_rasi = planets['mercury']['rasi_index']
    jupi_rasi = planets['jupiter']['rasi_index']
    venu_rasi = planets['venus']['rasi_index']
    satu_rasi = planets['saturn']['rasi_index']

    sun_house  = planet_house(sun_rasi)
    moon_house = planet_house(moon_rasi)
    mars_house = planet_house(mars_rasi)
    merc_house = planet_house(merc_rasi)
    jupi_house = planet_house(jupi_rasi)
    venu_house = planet_house(venu_rasi)
    satu_house = planet_house(satu_rasi)

    # 1. GAJAKESARI YOGA
    # Jupiter in kendra from Moon
    jupi_from_moon = ((jupi_rasi - moon_rasi) % 12) + 1
    if jupi_from_moon in KENDRA:
        yogas_found.append({
            'name':        'Gajakesari Yoga',
            'type':        'Benefic',
            'description': 'Jupiter in kendra from Moon. Grants intelligence, fame, and prosperity.',
            'planets':     ['Jupiter', 'Moon'],
        })

    # 2. BUDHA-ADITYA YOGA
    # Sun and Mercury in same sign
    if sun_rasi == merc_rasi:
        yogas_found.append({
            'name':        'Budha-Aditya Yoga',
            'type':        'Benefic',
            'description': 'Sun and Mercury conjunct. Grants sharp intellect, communication skills.',
            'planets':     ['Sun', 'Mercury'],
        })

    # 3. CHANDRA-MANGALA YOGA
    # Moon and Mars conjunct or in mutual 7th
    if moon_rasi == mars_rasi or abs(moon_rasi - mars_rasi) == 6:
        yogas_found.append({
            'name':        'Chandra-Mangala Yoga',
            'type':        'Mixed',
            'description': 'Moon and Mars in conjunction or opposition. Gives financial drive but emotional intensity.',
            'planets':     ['Moon', 'Mars'],
        })

    # 4. PANCHA MAHAPURUSHA YOGAS
    mahapurusha_planets = {
        'mars':    ('Ruchaka',    'Courage, leadership, land/property gains'),
        'mercury': ('Bhadra',     'Intelligence, communication, business acumen'),
        'jupiter': ('Hamsa',      'Wisdom, spirituality, fame, good fortune'),
        'venus':   ('Malavya',    'Beauty, luxury, artistic talent, marital happiness'),
        'saturn':  ('Shasha',     'Power, authority, longevity, discipline'),
    }
    planet_houses = {
        'mars': mars_house, 'mercury': merc_house,
        'jupiter': jupi_house, 'venus': venu_house, 'saturn': satu_house
    }
    planet_rasis = {
        'mars': mars_rasi, 'mercury': merc_rasi,
        'jupiter': jupi_rasi, 'venus': venu_rasi, 'saturn': satu_rasi
    }

    for planet, (yoga_name, description) in mahapurusha_planets.items():
        p_house = planet_houses[planet]
        p_rasi  = planet_rasis[planet]
        in_kendra = p_house in KENDRA
        in_own    = p_rasi in OWN_SIGN.get(planet, [])
        in_exalt  = p_rasi == EXALTATION.get(planet)

        if in_kendra and (in_own or in_exalt):
            yogas_found.append({
                'name':        f'{yoga_name} Yoga',
                'type':        'Mahapurusha (Benefic)',
                'description': description,
                'planets':     [planet.capitalize()],
            })

    # 5. KEMADRUMA YOGA
    # Moon has no planet in 2nd or 12th from it
    moon_2nd  = (moon_rasi + 1) % 12
    moon_12th = (moon_rasi - 1) % 12
    all_rasis = [sun_rasi, mars_rasi, merc_rasi, jupi_rasi, venu_rasi, satu_rasi]
    if moon_2nd not in all_rasis and moon_12th not in all_rasis:
        yogas_found.append({
            'name':        'Kemadruma Yoga',
            'type':        'Malefic',
            'description': 'Moon isolated with no planets in 2nd or 12th. May cause hardships, loneliness.',
            'planets':     ['Moon'],
        })

    # 6. NEECHA BHANGA RAJA YOGA
    # Debilitated planet's dispositor is in kendra from Lagna or Moon
    for planet, debil_sign in DEBILITATION.items():
        if planet_rasis.get(planet) == debil_sign or (planet == 'sun' and sun_rasi == debil_sign) or (planet == 'moon' and moon_rasi == debil_sign):
            yogas_found.append({
                'name':        f'Neecha Bhanga Raja Yoga ({planet.capitalize()})',
                'type':        'Cancellation of Debilitation (Benefic)',
                'description': f'{planet.capitalize()} is debilitated but gains strength through cancellation, turning weakness into power.',
                'planets':     [planet.capitalize()],
            })

    # 7. DHANA YOGAS
    # Lord of 2nd or 11th house connects with lord of 5th or 9th
    house_lord_map = {}
    for h in range(1, 13):
        sign_index = (asc_rasi + h - 1) % 12
        house_lord_map[h] = RASI_LORDS[sign_index]

    wealth_lords  = {house_lord_map[2], house_lord_map[11]}
    fortune_lords = {house_lord_map[5], house_lord_map[9]}

    if wealth_lords & fortune_lords:
        common = wealth_lords & fortune_lords
        yogas_found.append({
            'name':        'Dhana Yoga',
            'type':        'Benefic',
            'description': 'Lords of wealth houses (2nd/11th) connect with lords of fortune houses (5th/9th). Strong wealth potential.',
            'planets':     list(common),
        })

    return {
        'ascendant_rasi': RASI_NAMES[asc_rasi],
        'yogas_found':    len(yogas_found),
        'yogas':          yogas_found,
    }


# ─── ASHTAKAVARGA ──────────────────────────────────────────────────
def get_ashtakavarga(jd, latitude, longitude):
    """
    Correct Parashari Ashtakavarga.
    
    For each planet P, each contributor C (7 planets + Lagna) contributes
    a point to specific houses counted FROM C's own position.
    The tables below are from Brihat Parashara Hora Shastra.
    """
    planets = get_planet_positions(jd)
    houses  = get_ascendant_and_houses(jd, latitude, longitude)

    asc_rasi  = houses['ascendant']['rasi_index']
    p = {
        'sun':      planets['sun']['rasi_index'],
        'moon':     planets['moon']['rasi_index'],
        'mars':     planets['mars']['rasi_index'],
        'mercury':  planets['mercury']['rasi_index'],
        'jupiter':  planets['jupiter']['rasi_index'],
        'venus':    planets['venus']['rasi_index'],
        'saturn':   planets['saturn']['rasi_index'],
        'lagna':    asc_rasi,
    }

    # BPHS Ashtakavarga tables
    # Format: {planet_being_scored: {contributor: [benefic offsets from contributor]}}
    # Offsets are 1-based house positions FROM the contributor
    AVARGA_TABLES = {
        'sun': {
            'sun':     [1, 2, 4, 7, 8, 9, 10, 11],
            'moon':    [3, 6, 10, 11],
            'mars':    [1, 2, 4, 7, 8, 9, 10, 11],
            'mercury': [3, 5, 6, 9, 10, 11, 12],
            'jupiter': [5, 6, 9, 11],
            'venus':   [6, 7, 12],
            'saturn':  [1, 2, 4, 7, 8, 9, 10, 11],
            'lagna':   [3, 4, 6, 10, 11, 12],
        },
        'moon': {
            'sun':     [3, 6, 7, 8, 10, 11],
            'moon':    [1, 3, 6, 7, 10, 11],
            'mars':    [2, 3, 5, 6, 9, 10, 11],
            'mercury': [1, 3, 4, 5, 7, 8, 10, 11],
            'jupiter': [1, 4, 7, 8, 10, 11, 12],
            'venus':   [3, 4, 5, 7, 9, 10, 11],
            'saturn':  [3, 5, 6, 11],
            'lagna':   [3, 6, 10, 11],
        },
        'mars': {
            'sun':     [3, 5, 6, 10, 11],
            'moon':    [3, 6, 11],
            'mars':    [1, 2, 4, 7, 8, 10, 11],
            'mercury': [3, 5, 6, 11],
            'jupiter': [6, 10, 11, 12],
            'venus':   [6, 8, 11, 12],
            'saturn':  [1, 4, 7, 8, 9, 10, 11],
            'lagna':   [1, 3, 6, 10, 11],
        },
        'mercury': {
            'sun':     [5, 6, 9, 11, 12],
            'moon':    [2, 4, 6, 8, 10, 11],
            'mars':    [1, 2, 4, 7, 8, 9, 10, 11],
            'mercury': [1, 3, 5, 6, 9, 10, 11, 12],
            'jupiter': [6, 8, 11, 12],
            'venus':   [1, 2, 3, 4, 5, 8, 9, 11],
            'saturn':  [1, 2, 4, 7, 8, 9, 10, 11],
            'lagna':   [1, 2, 4, 6, 8, 10, 11],
        },
        'jupiter': {
            'sun':     [1, 2, 3, 4, 7, 8, 9, 10, 11],
            'moon':    [2, 5, 7, 9, 11],
            'mars':    [1, 2, 4, 7, 8, 10, 11],
            'mercury': [1, 2, 4, 5, 6, 9, 10, 11],
            'jupiter': [1, 2, 3, 4, 7, 8, 10, 11],
            'venus':   [2, 5, 6, 9, 10, 11],
            'saturn':  [3, 5, 6, 12],
            'lagna':   [1, 2, 4, 5, 6, 7, 9, 10, 11],
        },
        'venus': {
            'sun':     [8, 11, 12],
            'moon':    [1, 2, 3, 4, 5, 8, 9, 11, 12],
            'mars':    [3, 4, 6, 9, 11, 12],
            'mercury': [3, 5, 6, 9, 11],
            'jupiter': [5, 8, 9, 10, 11],
            'venus':   [1, 2, 3, 4, 5, 8, 9, 10, 11],
            'saturn':  [3, 4, 5, 8, 9, 10, 11],
            'lagna':   [1, 2, 3, 4, 5, 8, 9, 11],
        },
        'saturn': {
            'sun':     [1, 2, 4, 7, 8, 10, 11],
            'moon':    [3, 6, 11],
            'mars':    [3, 5, 6, 10, 11, 12],
            'mercury': [6, 8, 9, 10, 11, 12],
            'jupiter': [5, 6, 11, 12],
            'venus':   [6, 11, 12],
            'saturn':  [3, 5, 6, 11],
            'lagna':   [1, 3, 4, 6, 10, 11],
        },
    }

    planet_avarga = {}
    sarva = [0] * 12

    for planet_name, contributor_table in AVARGA_TABLES.items():
        scores = [0] * 12

        for contributor, benefic_offsets in contributor_table.items():
            ref_rasi = p[contributor]
            for offset in benefic_offsets:
                benefic_sign = (ref_rasi + offset - 1) % 12
                scores[benefic_sign] += 1

        planet_avarga[planet_name] = {
            'scores': scores,
            'total':  sum(scores),
            'signs': [
                {
                    'rasi':     RASI_NAMES[i],
                    'score':    scores[i],
                    'strength': 'Strong' if scores[i] >= 5 else ('Moderate' if scores[i] >= 3 else 'Weak')
                }
                for i in range(12)
            ]
        }

        for i in range(12):
            sarva[i] += scores[i]

    sarvashtakavarga = {
        'scores': sarva,
        'total':  sum(sarva),
        'signs': [
            {
                'rasi':     RASI_NAMES[i],
                'score':    sarva[i],
                'strength': 'Strong' if sarva[i] >= 30 else ('Moderate' if sarva[i] >= 25 else 'Weak')
            }
            for i in range(12)
        ]
    }

    return {
        'bhinnashtakavarga': planet_avarga,
        'sarvashtakavarga':  sarvashtakavarga,
    }


# ─── PHASE 4: KUNDALI MILAN ────────────────────────────────────────

# Nakshatra lords in Vimshottari order (for Koota calculations)
NAK_LORD = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

# Gana classification per nakshatra (0=Deva, 1=Manushya, 2=Rakshasa)
NAK_GANA = [
    0, 2, 0, 0, 0, 2, 0, 0, 2,  # Ashwini–Ashlesha
    2, 2, 0, 0, 2, 0, 2, 0, 2,  # Magha–Jyeshtha
    2, 0, 0, 0, 2, 0, 0, 0, 0   # Mula–Revati
]
GANA_NAMES = ["Deva", "Manushya", "Rakshasa"]

# Nadi classification per nakshatra (0=Aadi, 1=Madhya, 2=Antya)
NAK_NADI = [
    0, 1, 2, 2, 1, 0, 0, 1, 2,
    0, 1, 2, 2, 1, 0, 0, 1, 2,
    0, 1, 2, 2, 1, 0, 0, 1, 2
]
NADI_NAMES = ["Aadi", "Madhya", "Antya"]

# Yoni (animal symbol) per nakshatra — 14 yoni pairs
NAK_YONI = [
    0, 12, 9, 4, 10, 10, 7, 7, 6,
    13, 13, 3, 3, 11, 8, 11, 1, 2,
    5, 5, 8, 6, 12, 0, 2, 4, 9
]
YONI_NAMES = [
    "Horse", "Elephant", "Sheep", "Snake", "Dog",
    "Cat", "Rat", "Cow", "Buffalo", "Tiger",
    "Hare", "Monkey", "Lion", "Mongoose"
]
# Friendly yoni pairs (index pairs that are compatible)
YONI_FRIENDLY = {
    (0, 0), (1, 1), (2, 2), (3, 3), (4, 4),
    (5, 5), (6, 6), (7, 7), (8, 8), (9, 9),
    (10, 10), (11, 11), (12, 12), (13, 13),
    # Natural allies
    (0, 3), (3, 0),   # Horse-Snake (neutral in some texts, included here)
    (1, 2), (2, 1),   # Elephant-Sheep
    (4, 5), (5, 4),   # Dog-Cat (enemies in some texts — handled in scoring)
}
YONI_ENEMY = {
    (0, 9), (9, 0),   # Horse-Tiger
    (1, 13), (13, 1), # Elephant-Mongoose
    (4, 9), (9, 4),   # Dog-Tiger
    (6, 5), (5, 6),   # Rat-Cat
    (7, 12), (12, 7), # Cow-Lion
    (8, 12), (12, 8), # Buffalo-Lion
    (10, 4), (4, 10), # Hare-Dog
    (11, 0), (0, 11), # Monkey-Horse
}

# Rasi elements for Bhakoot calculation
# 0=Fire, 1=Earth, 2=Air, 3=Water
RASI_ELEMENT = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]

# Rasi lords
RASI_LORD = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

# Varna (social order) per rasi: 0=Brahmin, 1=Kshatriya, 2=Vaishya, 3=Shudra
RASI_VARNA = [1, 3, 2, 0, 1, 2, 0, 1, 0, 3, 3, 0]
VARNA_NAMES = ["Brahmin", "Kshatriya", "Vaishya", "Shudra"]

# Vasya groups: which signs are attracted to which
# 0=Chatushpada, 1=Manava, 2=Jalchar, 3=Vanchar, 4=Keeta
RASI_VASYA = [0, 1, 1, 2, 0, 1, 1, 3, 1, 0, 1, 4]
VASYA_NAMES = ["Chatushpada", "Manava", "Jalchar", "Vanchar", "Keeta"]

# Vasya compatibility table (who controls whom)
VASYA_ATTRACTED = {
    0: [1],     # Chatushpada (Aries/Leo/Capricorn/half-Sagittarius) → Manava
    1: [2, 4],  # Manava → Jalchar, Keeta
    2: [0, 1],  # Jalchar → Chatushpada, Manava
    3: [1],     # Vanchar → Manava
    4: [1],     # Keeta → Manava
}

# Planetary friendship table for Graha Maitri
PLANET_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus"],
}
PLANET_NEUTRAL = {
    "Sun":     ["Mercury"],
    "Moon":    ["Mars", "Jupiter", "Venus", "Saturn"],
    "Mars":    ["Venus", "Saturn"],
    "Mercury": ["Mars", "Jupiter", "Saturn"],
    "Jupiter": ["Saturn"],
    "Venus":   ["Mars", "Jupiter", "Moon"],
    "Saturn":  ["Jupiter", "Mars"],
}


def _get_nak_data(jd):
    """Helper: returns nakshatra index (0-26) and rasi index for Moon."""
    moon_long  = get_moon_longitude(jd)
    nak_index  = int(moon_long / (360 / 27))
    rasi_index = int(moon_long / 30)
    return nak_index, rasi_index


def _planet_relationship(lord1, lord2):
    """Returns relationship between two rasi lords: Friend/Neutral/Enemy."""
    if lord1 == lord2:
        return "Same"
    if lord2 in PLANET_FRIENDS.get(lord1, []):
        return "Friend"
    if lord2 in PLANET_NEUTRAL.get(lord1, []):
        return "Neutral"
    return "Enemy"


def calculate_ashtakoot(jd1, jd2):
    """
    Calculate all 8 Kootas of Ashtakoot Guna Milan.

    Returns each koota's score, max, result, and description.
    Total max = 36 points.

    The 8 Kootas:
    1. Varna     (1 pt)  — spiritual compatibility
    2. Vasya     (2 pts) — dominance/attraction
    3. Tara      (3 pts) — destiny/health
    4. Yoni      (4 pts) — physical/intimate compatibility
    5. Graha Maitri (5 pts) — mental compatibility
    6. Gana      (6 pts) — temperament
    7. Bhakoot   (7 pts) — emotional/family compatibility
    8. Nadi      (8 pts) — health/progeny
    """
    nak1, rasi1 = _get_nak_data(jd1)
    nak2, rasi2 = _get_nak_data(jd2)

    results = []

    # ── 1. VARNA (max 1) ───────────────────────────────────────────
    # Groom's varna >= Bride's varna = compatible
    varna1 = RASI_VARNA[rasi1]
    varna2 = RASI_VARNA[rasi2]
    # Lower index = higher varna (Brahmin=0 is highest)
    if varna1 <= varna2:
        varna_score = 1
        varna_result = "Compatible"
    else:
        varna_score = 0
        varna_result = "Incompatible — groom's varna lower than bride's"

    results.append({
        'koota':       'Varna',
        'max':         1,
        'score':       varna_score,
        'result':      varna_result,
        'boy_varna':   VARNA_NAMES[varna1],
        'girl_varna':  VARNA_NAMES[varna2],
        'description': 'Spiritual and ego compatibility.',
    })

    # ── 2. VASYA (max 2) ────────────────────────────────────────────
    vasya1 = RASI_VASYA[rasi1]
    vasya2 = RASI_VASYA[rasi2]
    if vasya1 == vasya2:
        vasya_score = 2
        vasya_result = "Same group — full score"
    elif vasya2 in VASYA_ATTRACTED.get(vasya1, []):
        vasya_score = 2
        vasya_result = "Boy attracts girl"
    elif vasya1 in VASYA_ATTRACTED.get(vasya2, []):
        vasya_score = 1
        vasya_result = "Girl attracts boy — partial score"
    else:
        vasya_score = 0
        vasya_result = "No vasya attraction"

    results.append({
        'koota':       'Vasya',
        'max':         2,
        'score':       vasya_score,
        'result':      vasya_result,
        'boy_vasya':   VASYA_NAMES[vasya1],
        'girl_vasya':  VASYA_NAMES[vasya2],
        'description': 'Mutual attraction and control.',
    })

    # ── 3. TARA (max 3) ─────────────────────────────────────────────
    # Count nakshatras from boy to girl and girl to boy
    # Divide by 9, check remainder: 1,3,5,7 = auspicious
    AUSPICIOUS_TARA = {1, 3, 5, 7}
    tara_b2g = ((nak2 - nak1) % 27) + 1
    tara_g2b = ((nak1 - nak2) % 27) + 1
    remainder_b2g = ((tara_b2g - 1) % 9) + 1
    remainder_g2b = ((tara_g2b - 1) % 9) + 1

    boy_auspicious  = remainder_b2g in AUSPICIOUS_TARA
    girl_auspicious = remainder_g2b in AUSPICIOUS_TARA

    if boy_auspicious and girl_auspicious:
        tara_score = 3
        tara_result = "Both auspicious"
    elif boy_auspicious or girl_auspicious:
        tara_score = 1.5
        tara_result = "One side auspicious"
    else:
        tara_score = 0
        tara_result = "Both inauspicious"

    results.append({
        'koota':          'Tara',
        'max':            3,
        'score':          tara_score,
        'result':         tara_result,
        'boy_tara':       remainder_b2g,
        'girl_tara':      remainder_g2b,
        'description':    'Destiny, health, and well-being after marriage.',
    })

    # ── 4. YONI (max 4) ─────────────────────────────────────────────
    yoni1 = NAK_YONI[nak1]
    yoni2 = NAK_YONI[nak2]
    pair  = (yoni1, yoni2)

    if yoni1 == yoni2:
        yoni_score = 4
        yoni_result = "Same yoni — best"
    elif pair in YONI_ENEMY:
        yoni_score = 0
        yoni_result = "Enemy yoni — incompatible"
    elif pair in YONI_FRIENDLY:
        yoni_score = 3
        yoni_result = "Friendly yoni"
    else:
        yoni_score = 2
        yoni_result = "Neutral yoni"

    results.append({
        'koota':      'Yoni',
        'max':        4,
        'score':      yoni_score,
        'result':     yoni_result,
        'boy_yoni':   YONI_NAMES[yoni1],
        'girl_yoni':  YONI_NAMES[yoni2],
        'description':'Physical and intimate compatibility.',
    })

    # ── 5. GRAHA MAITRI (max 5) ─────────────────────────────────────
    lord1 = RASI_LORD[rasi1]
    lord2 = RASI_LORD[rasi2]
    rel_b2g = _planet_relationship(lord1, lord2)
    rel_g2b = _planet_relationship(lord2, lord1)

    if rel_b2g == "Same":
        maitri_score = 5
        maitri_result = "Same rasi lord — best"
    elif rel_b2g == "Friend" and rel_g2b == "Friend":
        maitri_score = 5
        maitri_result = "Mutual friends"
    elif rel_b2g == "Friend" or rel_g2b == "Friend":
        maitri_score = 4
        maitri_result = "One-sided friendship"
    elif rel_b2g == "Neutral" and rel_g2b == "Neutral":
        maitri_score = 3
        maitri_result = "Both neutral"
    elif rel_b2g == "Neutral" or rel_g2b == "Neutral":
        maitri_score = 1
        maitri_result = "One neutral, one enemy"
    else:
        maitri_score = 0
        maitri_result = "Mutual enemies"

    results.append({
        'koota':        'Graha Maitri',
        'max':          5,
        'score':        maitri_score,
        'result':       maitri_result,
        'boy_lord':     lord1,
        'girl_lord':    lord2,
        'relationship': f"Boy→Girl: {rel_b2g}, Girl→Boy: {rel_g2b}",
        'description':  'Mental compatibility and friendship between minds.',
    })

    # ── 6. GANA (max 6) ─────────────────────────────────────────────
    gana1 = NAK_GANA[nak1]
    gana2 = NAK_GANA[nak2]

    if gana1 == gana2:
        gana_score = 6
        gana_result = "Same Gana — best"
    elif (gana1 == 0 and gana2 == 1) or (gana1 == 1 and gana2 == 0):
        gana_score = 5
        gana_result = "Deva-Manushya — compatible"
    elif (gana1 == 1 and gana2 == 2) or (gana1 == 2 and gana2 == 1):
        gana_score = 1
        gana_result = "Manushya-Rakshasa — low compatibility"
    else:
        # Deva-Rakshasa
        gana_score = 0
        gana_result = "Deva-Rakshasa — incompatible"

    results.append({
        'koota':      'Gana',
        'max':        6,
        'score':      gana_score,
        'result':     gana_result,
        'boy_gana':   GANA_NAMES[gana1],
        'girl_gana':  GANA_NAMES[gana2],
        'description':'Temperament and nature compatibility.',
    })

    # ── 7. BHAKOOT (max 7) ──────────────────────────────────────────
    # Count rasi positions between partners
    # Inauspicious combinations: 6-8, 5-9, 3-11 from each other
    rasi_diff_b2g = ((rasi2 - rasi1) % 12) + 1
    rasi_diff_g2b = ((rasi1 - rasi2) % 12) + 1

    INAUSPICIOUS_BHAKOOT = {6, 8, 5, 9}  # 3-11 is debated, excluded here

    if rasi_diff_b2g in INAUSPICIOUS_BHAKOOT or rasi_diff_g2b in INAUSPICIOUS_BHAKOOT:
        bhakoot_score = 0
        bhakoot_result = f"Inauspicious — {rasi_diff_b2g}-{rasi_diff_g2b} combination"
    else:
        bhakoot_score = 7
        bhakoot_result = "Auspicious"

    results.append({
        'koota':       'Bhakoot',
        'max':         7,
        'score':       bhakoot_score,
        'result':      bhakoot_result,
        'boy_rasi':    RASI_NAMES[rasi1],
        'girl_rasi':   RASI_NAMES[rasi2],
        'rasi_diff':   f"{rasi_diff_b2g}-{rasi_diff_g2b}",
        'description': 'Emotional and family well-being after marriage.',
    })

    # ── 8. NADI (max 8) ─────────────────────────────────────────────
    nadi1 = NAK_NADI[nak1]
    nadi2 = NAK_NADI[nak2]

    if nadi1 == nadi2:
        nadi_score = 0
        nadi_result = f"Same Nadi ({NADI_NAMES[nadi1]}) — Nadi Dosha present"
    else:
        nadi_score = 8
        nadi_result = "Different Nadi — full score"

    results.append({
        'koota':      'Nadi',
        'max':        8,
        'score':      nadi_score,
        'result':     nadi_result,
        'boy_nadi':   NADI_NAMES[nadi1],
        'girl_nadi':  NADI_NAMES[nadi2],
        'description':'Health, progeny, and genetic compatibility. Most critical koota.',
    })

    # ── TOTAL ────────────────────────────────────────────────────────
    total_score = sum(k['score'] for k in results)

    if total_score >= 32:
        compatibility = "Excellent"
        recommendation = "Highly recommended match"
    elif total_score >= 24:
        compatibility = "Good"
        recommendation = "Recommended match"
    elif total_score >= 18:
        compatibility = "Average"
        recommendation = "Acceptable match — consult an astrologer"
    else:
        compatibility = "Poor"
        recommendation = "Not recommended without remedies"

    return {
        'total_score':     total_score,
        'max_score':       36,
        'percentage':      round((total_score / 36) * 100, 1),
        'compatibility':   compatibility,
        'recommendation':  recommendation,
        'kootas':          results,
    }


def check_mangal_dosha(jd, latitude, longitude):
    """
    Detect Mangal Dosha (Kuja Dosha) from the birth chart.

    Mars in houses 1, 2, 4, 7, 8, or 12 from Lagna causes Mangal Dosha.
    Some traditions also check from Moon and Venus ascendants.

    Exceptions (cancellations) are also checked.
    """
    planets = get_planet_positions(jd)
    houses  = get_ascendant_and_houses(jd, latitude, longitude)

    asc_rasi  = houses['ascendant']['rasi_index']
    mars_rasi = planets['mars']['rasi_index']
    moon_rasi = planets['moon']['rasi_index']
    venus_rasi = planets['venus']['rasi_index']

    DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}

    def house_of(planet_rasi, ref_rasi):
        return ((planet_rasi - ref_rasi) % 12) + 1

    mars_from_lagna = house_of(mars_rasi, asc_rasi)
    mars_from_moon  = house_of(mars_rasi, moon_rasi)
    mars_from_venus = house_of(mars_rasi, venus_rasi)

    dosha_from_lagna = mars_from_lagna in DOSHA_HOUSES
    dosha_from_moon  = mars_from_moon  in DOSHA_HOUSES
    dosha_from_venus = mars_from_venus in DOSHA_HOUSES

    # Cancellation conditions
    cancellations = []

    # Mars in own sign (Aries/Scorpio) or exaltation (Capricorn)
    if mars_rasi in [0, 7, 9]:
        cancellations.append("Mars in own sign or exaltation — dosha cancelled")

    # Mars in 2nd house and 2nd lord strong
    if mars_from_lagna == 2:
        cancellations.append("Mars in 2nd — some traditions exempt this")

    # Jupiter aspects Mars (Jupiter 5th/7th/9th from Mars)
    jupi_rasi = planets['jupiter']['rasi_index']
    jupi_from_mars = house_of(jupi_rasi, mars_rasi)
    if jupi_from_mars in [5, 7, 9]:
        cancellations.append("Jupiter aspects Mars — reduces dosha intensity")

    # Both partners have Mangal Dosha — cancels each other
    # (handled at compatibility level, noted here)

    has_dosha = dosha_from_lagna  # Primary check

    return {
        'has_mangal_dosha':     has_dosha,
        'mars_house_lagna':     mars_from_lagna,
        'mars_house_moon':      mars_from_moon,
        'mars_house_venus':     mars_from_venus,
        'dosha_from_lagna':     dosha_from_lagna,
        'dosha_from_moon':      dosha_from_moon,
        'dosha_from_venus':     dosha_from_venus,
        'cancellations':        cancellations,
        'severity':             'High' if dosha_from_lagna and dosha_from_moon else
                                'Medium' if dosha_from_lagna or dosha_from_moon else 'None',
        'mars_rasi':            RASI_NAMES[mars_rasi],
        'ascendant_rasi':       RASI_NAMES[asc_rasi],
    }


# ─── PHASE 5: GOCHAR (TRANSITS) ────────────────────────────────────

# Transit interpretations for each planet through each house
# Format: (house_number): (effect)
TRANSIT_EFFECTS = {
    'sun': {
        1:  "Self-focus, health matters, new beginnings",
        2:  "Financial gains, family focus, speech matters",
        3:  "Courage, travel, siblings, communication",
        4:  "Home, mother, emotional matters, vehicles",
        5:  "Children, creativity, education, romance",
        6:  "Victory over enemies, health improvements",
        7:  "Partnerships, marriage matters, public dealings",
        8:  "Obstacles, hidden matters, transformation",
        9:  "Luck, spirituality, father, long journeys",
        10: "Career peak, authority, public recognition",
        11: "Gains, income, social circle, elder siblings",
        12: "Expenses, isolation, foreign travel, losses",
    },
    'moon': {
        1:  "Good health, travel, emotional sensitivity",
        2:  "Financial gains, family harmony, good food",
        3:  "Short journeys, courage, siblings connect",
        4:  "Home comfort, mother's wellbeing, happiness",
        5:  "Romance, children matters, creative spark",
        6:  "Health issues possible, conflicts with rivals",
        7:  "Social life, partnerships, meeting people",
        8:  "Emotional turbulence, avoid risky decisions",
        9:  "Spiritual pursuits, pilgrimages, good fortune",
        10: "Career gains, public image boost",
        11: "Gains, social success, wish fulfillment",
        12: "Rest, isolation, spiritual retreat, expenses",
    },
    'mars': {
        1:  "Energy boost, assertiveness, possible conflicts",
        2:  "Expenses on family, speech issues, financial stress",
        3:  "Courage, short travels, sibling matters",
        4:  "Domestic tension, property matters, vehicle issues",
        5:  "Children concerns, speculation risks",
        6:  "Victory over enemies, good for health",
        7:  "Relationship conflicts, partner's health concerns",
        8:  "Accidents risk, health issues, transformation",
        9:  "Father's health, travel, religious matters",
        10: "Career drive, ambition peak, workplace conflicts",
        11: "Income gains, social energy, elder sibling matters",
        12: "Expenses, hidden enemies, foreign matters",
    },
    'jupiter': {
        1:  "Personal growth, wisdom, health improvement",
        2:  "Wealth accumulation, family blessings, speech",
        3:  "Short journeys, sibling prosperity, courage",
        4:  "Home expansion, mother's wellbeing, property",
        5:  "Children blessings, education success, romance",
        6:  "Service, health issues resolution, debts cleared",
        7:  "Marriage blessings, partnerships flourish",
        8:  "Hidden knowledge, occult, inheritance possible",
        9:  "Best transit — luck, spirituality, guru blessings",
        10: "Career expansion, promotions, authority",
        11: "Maximum gains, income surge, wishes fulfilled",
        12: "Spiritual growth, foreign travel, moksha themes",
    },
    'saturn': {
        1:  "Sade Sati peak — hard work, health focus, delays",
        2:  "Financial caution, family responsibilities",
        3:  "Effort rewarded slowly, sibling matters",
        4:  "Home stress, mother's health, vehicle issues",
        5:  "Children matters, creative blocks, education delays",
        6:  "Discipline wins, health improvement, enemy defeat",
        7:  "Relationship tests, partner's hardships",
        8:  "Chronic illness risk, hidden obstacles",
        9:  "Father's health, spiritual discipline, travel delays",
        10: "Career discipline, slow but steady progress",
        11: "Gains after effort, delayed income",
        12: "Isolation, spiritual discipline, foreign stays",
    },
    'mercury': {
        1:  "Sharp intellect, communication boost, travel",
        2:  "Financial planning, education, speech gains",
        3:  "Writing, travel, sibling communication",
        4:  "Home education, mother communication",
        5:  "Intellectual creativity, children education",
        6:  "Problem-solving, health analysis",
        7:  "Business partnerships, negotiations",
        8:  "Research, occult studies, tax matters",
        9:  "Higher education, publishing, long travel",
        10: "Career communication, presentations",
        11: "Income from intellect, social networking",
        12: "Foreign communication, spiritual study",
    },
    'venus': {
        1:  "Charm, beauty, romantic attention",
        2:  "Wealth inflow, family harmony, luxuries",
        3:  "Artistic pursuits, social travel, siblings",
        4:  "Home beautification, mother's joy, comfort",
        5:  "Romance peak, creativity, children joy",
        6:  "Health through beauty, rivals subdued",
        7:  "Marriage blessings, partnership harmony",
        8:  "Sensual pleasures, hidden relationships",
        9:  "Luxurious travel, religious art, fortunate",
        10: "Career in arts/beauty, public admiration",
        11: "Social gains, income from beauty/arts",
        12: "Pleasures in isolation, foreign romance",
    },
    'rahu': {
        1:  "Unusual events, ambition surge, identity shifts",
        2:  "Unconventional income, foreign food/speech",
        3:  "Fearless action, unusual travel, media",
        4:  "Property matters, foreign residence, home changes",
        5:  "Speculative gains/losses, unconventional romance",
        6:  "Victory over enemies through unusual means",
        7:  "Foreign/unconventional partnerships",
        8:  "Sudden transformation, occult interests",
        9:  "Foreign religion/philosophy, unusual beliefs",
        10: "Sudden career rise, unconventional fame",
        11: "Large gains, foreign income, unusual friends",
        12: "Foreign lands, spiritual confusion, isolation",
    },
    'ketu': {
        1:  "Detachment from self, spiritual awakening",
        2:  "Financial detachment, speech issues",
        3:  "Short spiritual journeys, detachment from siblings",
        4:  "Home detachment, mother's spiritual matters",
        5:  "Past life karma with children, detachment",
        6:  "Karmic health issues, service orientation",
        7:  "Spiritual partnerships, detachment from marriage",
        8:  "Moksha themes, deep transformation",
        9:  "Spiritual pilgrimages, guru karma",
        10: "Career detachment, spiritual fame",
        11: "Detachment from gains, spiritual income",
        12: "Moksha, liberation, deep spiritual retreat",
    },
}

# Ashtakavarga transit scores threshold for good transit
GOOD_TRANSIT_THRESHOLD = 4


def get_current_jd():
    """Get Julian Day for current UTC time."""
    now = dt.datetime.utcnow()
    return swe.julday(now.year, now.month, now.day,
                      now.hour + now.minute / 60.0 + now.second / 3600.0)


def get_transit_positions(transit_jd):
    """
    Get all planet positions for a given Julian Day (transit time).
    Returns sidereal positions using Lahiri ayanamsa.
    """
    return get_planet_positions(transit_jd)


def analyze_transits(natal_jd, transit_jd, natal_lat, natal_lon):
    """
    Compare transit planet positions against natal chart houses.

    For each transiting planet:
    - Find which natal house it occupies
    - Look up the classical effect
    - Check Ashtakavarga score for that sign
    - Flag if it's transiting natal planet positions (conjunctions)
    """
    natal_houses  = get_ascendant_and_houses(natal_jd, natal_lat, natal_lon)
    natal_planets = get_planet_positions(natal_jd)
    transit_planets = get_transit_positions(transit_jd)

    asc_rasi = natal_houses['ascendant']['rasi_index']

    # Get Ashtakavarga scores for transit strength
    avarga = get_ashtakavarga(natal_jd, natal_lat, natal_lon)

    transits = []

    for planet_name, t_data in transit_planets.items():
        if planet_name == 'ketu':
            continue  # Ketu = Rahu + 180, calculated from Rahu

        t_rasi   = t_data['rasi_index']
        t_house  = ((t_rasi - asc_rasi) % 12) + 1

        # Ashtakavarga score for this planet in the transiting sign
        avarga_score = None
        if planet_name in avarga['bhinnashtakavarga']:
            avarga_score = avarga['bhinnashtakavarga'][planet_name]['scores'][t_rasi]

        # Effect lookup
        effect = TRANSIT_EFFECTS.get(planet_name, {}).get(t_house, "Neutral transit")

        # Check conjunctions with natal planets (within 3° orb)
        conjunctions = []
        for n_planet, n_data in natal_planets.items():
            orb = abs(t_data['longitude'] - n_data['longitude'])
            if orb > 180:
                orb = 360 - orb
            if orb <= 3.0:
                conjunctions.append({
                    'natal_planet': n_planet,
                    'orb':          round(orb, 2),
                })

        # Overall favorability
        if avarga_score is not None:
            favorable = avarga_score >= GOOD_TRANSIT_THRESHOLD
        else:
            favorable = t_house in {2, 3, 6, 10, 11}  # Classical good houses

        transits.append({
            'planet':          planet_name,
            'transit_rasi':    t_data['rasi'],
            'transit_house':   t_house,
            'longitude':       t_data['longitude'],
            'retrograde':      t_data['retrograde'],
            'avarga_score':    avarga_score,
            'favorable':       favorable,
            'effect':          effect,
            'conjunctions':    conjunctions,
        })

    # Sort by planet importance
    order = ['jupiter', 'saturn', 'rahu', 'mars', 'sun', 'moon', 'mercury', 'venus']
    transits.sort(key=lambda x: order.index(x['planet']) if x['planet'] in order else 99)

    return transits


def get_sade_sati(natal_jd, transit_jd):
    """
    Check if the person is currently in Sade Sati or Dhaiya (Kantaka Shani).

    Sade Sati: Saturn transiting the sign before, same as,
               or after natal Moon sign (7.5 years total, 3 phases).
    Dhaiya:    Saturn in 4th or 8th from natal Moon (2.5 years each).
    """
    natal_planets   = get_planet_positions(natal_jd)
    transit_planets = get_transit_positions(transit_jd)

    moon_rasi    = natal_planets['moon']['rasi_index']
    saturn_rasi  = transit_planets['saturn']['rasi_index']

    diff = (saturn_rasi - moon_rasi) % 12

    in_sade_sati = diff in {0, 1, 11}   # same, next, previous sign
    in_dhaiya    = diff in {3, 7}        # 4th or 8th from Moon

    phase = None
    if diff == 11:
        phase = "Rising (1st phase) — Saturn in 12th from Moon"
    elif diff == 0:
        phase = "Peak (2nd phase) — Saturn on natal Moon sign"
    elif diff == 1:
        phase = "Setting (3rd phase) — Saturn in 2nd from Moon"

    dhaiya_type = None
    if diff == 3:
        dhaiya_type = "Kantaka Shani — Saturn in 4th from Moon"
    elif diff == 7:
        dhaiya_type = "Ashtama Shani — Saturn in 8th from Moon"

    return {
        'natal_moon_rasi':   RASI_NAMES[moon_rasi],
        'transit_saturn_rasi': RASI_NAMES[saturn_rasi],
        'in_sade_sati':      in_sade_sati,
        'sade_sati_phase':   phase,
        'in_dhaiya':         in_dhaiya,
        'dhaiya_type':       dhaiya_type,
        'saturn_from_moon':  diff + 1,   # 1-based house from Moon
    }


def get_moon_transit(transit_jd):
    """
    Get detailed Moon transit data — Chandra Gochar.
    Moon changes sign every ~2.25 days.
    Returns current nakshatra, rasi, and Chandra Ashtakavarga score.
    """
    init_ephe()
    flags     = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, _ = swe.calc_ut(transit_jd, swe.MOON, flags)

    moon_long = result[0]
    moon_speed = result[3]   # degrees/day

    rasi_index  = int(moon_long / 30)
    deg_in_rasi = moon_long % 30
    nak_index   = int(moon_long / (360 / 27))
    deg_in_nak  = moon_long % (360 / 27)
    pada        = int(deg_in_nak / (360 / 108)) + 1

    # Degrees remaining in current sign
    degrees_remaining = 30.0 - deg_in_rasi
    hours_remaining   = (degrees_remaining / abs(moon_speed)) * 24 if moon_speed != 0 else None

    # Next sign
    next_rasi_index = (rasi_index + 1) % 12

    return {
        'moon_longitude':      round(moon_long, 6),
        'rasi':                RASI_NAMES[rasi_index],
        'rasi_index':          rasi_index,
        'degree_in_rasi':      round(deg_in_rasi, 4),
        'nakshatra':           NAKSHATRA_NAMES[nak_index],
        'nakshatra_lord':      NAKSHATRA_LORDS[nak_index],
        'pada':                pada,
        'speed_deg_per_day':   round(moon_speed, 4),
        'degrees_to_next_sign': round(degrees_remaining, 4),
        'hours_to_next_sign':  round(hours_remaining, 1) if hours_remaining else None,
        'next_rasi':           RASI_NAMES[next_rasi_index],
    }