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

    D1  = Rasi (natal chart, division=1)
    D9  = Navamsa (division=9)  — spouse, dharma, inner self
    D10 = Dashamsa (division=10) — career, profession
    D2  = Hora
    D3  = Drekkana
    D12 = Dwadashamsa

    Formula: D-N position = floor(longitude % 30 / (30/N)) * (360/N/12)
    Then add to the starting sign based on odd/even sign rules.
    """
    init_ephe()

    planet_positions = get_planet_positions(jd)
    div_positions    = {}

    for planet_name, data in planet_positions.items():
        longitude   = data['longitude']
        rasi_index  = data['rasi_index']           # 0–11
        deg_in_rasi = data['degree_in_rasi']       # 0–30

        # Each rasi is divided into N equal parts of (30/N) degrees
        part_size   = 30.0 / division
        part_number = int(deg_in_rasi / part_size)  # 0-based part within rasi

        # D9 Navamsa rule: cycle of 12 signs starts from:
        # Fire signs  (Aries, Leo, Sag)     → start from Aries   (0)
        # Earth signs (Taurus, Virgo, Cap)  → start from Capricorn (9)
        # Air signs   (Gemini, Libra, Aqua) → start from Libra    (6)
        # Water signs (Cancer, Scorpio, Pis)→ start from Cancer   (3)
        if division == 9:
            element = rasi_index % 4
            start_map = {0: 0, 1: 9, 2: 6, 3: 3}   # Fire/Earth/Air/Water
            start_sign = start_map[element]
        elif division == 10:
            # D10: odd signs start from same sign, even signs start from 9th
            if rasi_index % 2 == 0:   # odd sign (1,3,5...)
                start_sign = rasi_index
            else:                      # even sign
                start_sign = (rasi_index + 8) % 12
        elif division == 2:
            # D2 Hora: Sun hora or Moon hora
            start_sign = 4 if rasi_index % 2 == 0 else 3  # Leo or Cancer
        elif division == 3:
            # D3 Drekkana: 1st=same sign, 2nd=5th, 3rd=9th
            start_sign = (rasi_index + part_number * 4) % 12
        elif division == 12:
            # D12: starts from same sign
            start_sign = rasi_index
        else:
            start_sign = 0

        div_rasi_index = (start_sign + part_number) % 12
        div_rasi       = RASI_NAMES[div_rasi_index]
        div_lord       = RASI_LORDS[div_rasi_index]

        div_positions[planet_name] = {
            'rasi':       div_rasi,
            'rasi_index': div_rasi_index,
            'lord':       div_lord,
            'original_longitude': round(longitude, 6),
        }

    # Ascendant in divisional chart
    asc_data    = get_ascendant_and_houses(jd, 0, 0)   # placeholder, recalc below
    asc_long    = asc_data['ascendant']['longitude']
    asc_rasi    = int(asc_long / 30)
    asc_deg     = asc_long % 30
    part_size   = 30.0 / division
    part_num    = int(asc_deg / part_size)

    if division == 9:
        element   = asc_rasi % 4
        start_map = {0: 0, 1: 9, 2: 6, 3: 3}
        start_sign = start_map[element]
    elif division == 10:
        start_sign = asc_rasi if asc_rasi % 2 == 0 else (asc_rasi + 8) % 12
    else:
        start_sign = asc_rasi

    div_asc_index = (start_sign + part_num) % 12

    return {
        'division':   division,
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