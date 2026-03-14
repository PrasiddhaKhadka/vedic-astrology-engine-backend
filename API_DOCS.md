# AstroGyan API — Full Documentation

**Base URL:** `http://localhost:8000/api/v1/`  
**Protocol:** HTTP POST  
**Content-Type:** `application/json`  
**Ayanamsa:** Lahiri (sidereal)  
**House System default:** Whole Sign  

---

## Table of Contents

1. [Input Reference](#input-reference)
2. [Phase 1 — Birth Chart](#phase-1--birth-chart)
3. [Phase 2 — Panchang & Dasha](#phase-2--panchang--dasha)
4. [Phase 3 — Advanced Charts](#phase-3--advanced-charts)
5. [Phase 4 — Compatibility](#phase-4--compatibility)
6. [Phase 5 — Transits](#phase-5--transits)
7. [Error Responses](#error-responses)
8. [Common Values Reference](#common-values-reference)

---

## Input Reference

### Standard Birth Data

Used by all chart, dasha, yoga, and transit endpoints.

```json
{
  "year":         1998,
  "month":        5,
  "day":          10,
  "hour":         10,
  "minute":       30,
  "latitude":     27.7172,
  "longitude":    85.3240,
  "utc_offset":   5.75,
  "house_system": "whole_sign"
}
```

**UTC Offset Examples:**
| Location | UTC Offset |
|----------|-----------|
| Nepal (NPT) | 5.75 |
| India (IST) | 5.5 |
| UK (GMT) | 0.0 |
| USA Eastern | -5.0 |
| USA Pacific | -8.0 |

**House Systems:**
- `whole_sign` — Standard for Vedic (default)
- `placidus` — Common in Western astrology
- `equal` — Equal house system
- `koch` — Koch house system

---

## Phase 1 — Birth Chart

---

### POST `/api/v1/chart/`

Full birth chart — planets + houses in one call. Most commonly used endpoint.

**Request:**
```json
{
  "year": 1998, "month": 5, "day": 10,
  "hour": 10, "minute": 30,
  "latitude": 27.7172, "longitude": 85.3240,
  "utc_offset": 5.75, "house_system": "whole_sign"
}
```

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "system": "Vedic (Sidereal)",
  "ascendant": {
    "longitude": 95.769942,
    "rasi": "Cancer",
    "rasi_index": 3,
    "degree_in_rasi": 5.7699
  },
  "midheaven": {
    "longitude": 358.44633,
    "rasi": "Pisces",
    "rasi_index": 11,
    "degree_in_rasi": 28.4463
  },
  "houses": [
    {
      "house": 1,
      "cusp_longitude": 90.0,
      "rasi": "Cancer",
      "rasi_index": 3,
      "degree_in_rasi": 0.0
    }
    // ... houses 2–12
  ],
  "house_system": "whole_sign",
  "planets": {
    "sun": {
      "longitude": 25.49901,
      "latitude": 0.000142,
      "speed": 0.966243,
      "retrograde": false,
      "rasi": "Aries",
      "rasi_index": 0,
      "degree_in_rasi": 25.499
    }
    // moon, mars, mercury, jupiter, venus, saturn, rahu, ketu
  }
}
```

**Planet fields:**
| Field | Description |
|-------|-------------|
| `longitude` | Sidereal ecliptic longitude (0–360°) |
| `latitude` | Ecliptic latitude |
| `speed` | Degrees per day (negative = retrograde) |
| `retrograde` | true/false |
| `rasi` | Zodiac sign name |
| `rasi_index` | 0=Aries, 1=Taurus ... 11=Pisces |
| `degree_in_rasi` | Degrees within the sign (0–30°) |

---

### POST `/api/v1/planets/`

Planet positions only. Same request body as `/chart/`.

---

### POST `/api/v1/houses/`

Ascendant + 12 house cusps only. Same request body as `/chart/`.

---

## Phase 2 — Panchang & Dasha

---

### POST `/api/v1/nakshatra/`

Moon's Nakshatra (birth star).

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "nakshatra": "Swati",
  "nakshatra_index": 15,
  "pada": 1,
  "lord": "Rahu",
  "moon_longitude": 189.814505,
  "degree_in_nakshatra": 3.1478
}
```

| Field | Description |
|-------|-------------|
| `nakshatra` | Nakshatra name (27 nakshatras) |
| `nakshatra_index` | 1–27 |
| `pada` | Quarter (1–4) |
| `lord` | Ruling planet of the nakshatra |
| `degree_in_nakshatra` | Degrees within nakshatra (0–13.33°) |

---

### POST `/api/v1/panchang/`

The 5 elements of Panchang.

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "tithi": {
    "name": "Chaturdashi",
    "paksha": "Shukla",
    "index": 14
  },
  "vara": {
    "name": "Sunday",
    "index": 0
  },
  "nakshatra": { ... },
  "yoga": {
    "name": "Vyatipata",
    "index": 17
  },
  "karana": {
    "name": "Vanija",
    "index": 6
  }
}
```

| Element | Description |
|---------|-------------|
| `tithi` | Lunar day (1–30). Paksha = Shukla (waxing) or Krishna (waning) |
| `vara` | Weekday (Sunday–Saturday) |
| `nakshatra` | Moon's star (see Nakshatra endpoint) |
| `yoga` | Sun+Moon combination (27 yogas) |
| `karana` | Half-tithi (11 karanas) |

---

### POST `/api/v1/dasha/`

Vimshottari Mahadasha periods for 120 years from birth.

**Response:**
```json
{
  "status": "success",
  "system": "Vimshottari",
  "total_years": 120,
  "moon_nakshatra": "Swati",
  "mahadasha": [
    {
      "lord": "Rahu",
      "start_date": "1998-05-10",
      "end_date": "2012-02-08",
      "years": 13.7504
    },
    {
      "lord": "Jupiter",
      "start_date": "2012-02-08",
      "end_date": "2028-02-08",
      "years": 16
    }
    // ... 9 total periods
  ]
}
```

---

## Phase 3 — Advanced Charts

---

### POST `/api/v1/antardasha/`

Vimshottari Mahadasha with nested Antardasha (sub-periods).
Returns 9 Mahadashas × 9 Antardashas = 81 total periods.

**Response structure:**
```json
{
  "status": "success",
  "system": "Vimshottari",
  "moon_nakshatra": "Swati",
  "mahadasha": [
    {
      "lord": "Rahu",
      "start_date": "1998-05-10",
      "end_date": "2012-02-04",
      "years": 13.7504,
      "antardasha": [
        {
          "lord": "Rahu",
          "start_date": "1998-05-10",
          "end_date": "2000-06-01",
          "years": 2.0626
        }
        // ... 9 antardashas
      ]
    }
    // ... 9 mahadashas
  ]
}
```

---

### POST `/api/v1/divisional/`

Divisional (Varga) charts. Pass a `division` field in the request.

**Additional field:**
```json
{ "division": 9 }
```

**Supported divisions:**

| Division | Chart Name | Purpose |
|----------|-----------|---------|
| 2 | Hora | Wealth and finances |
| 3 | Drekkana | Siblings and courage |
| 7 | Saptamsa | Children and progeny |
| 9 | Navamsa | Spouse, dharma, inner self |
| 10 | Dashamsa | Career and profession |
| 12 | Dwadashamsa | Parents and ancestors |
| 16 | Shodashamsa | Vehicles and comforts |
| 30 | Trimshamsa | Misfortunes and health |
| 60 | Shashtiamsa | Detailed karma (most sensitive) |

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "division": 9,
  "chart_name": "Navamsa",
  "purpose": "Spouse, dharma, inner self",
  "ascendant": {
    "rasi": "Taurus",
    "rasi_index": 1,
    "lord": "Venus"
  },
  "planets": {
    "sun": {
      "rasi": "Scorpio",
      "rasi_index": 7,
      "lord": "Mars",
      "original_longitude": 25.49901,
      "original_rasi": "Aries",
      "degree_in_rasi": 25.499
    }
    // ...
  }
}
```

> **Note:** D60 Shashtiamsa is extremely sensitive to birth time. Even a 1-minute difference can change planet positions.

---

### POST `/api/v1/yogas/`

Detects major Vedic Yogas in the birth chart.

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "ascendant_rasi": "Cancer",
  "yogas_found": 5,
  "yogas": [
    {
      "name": "Ruchaka Yoga",
      "type": "Mahapurusha (Benefic)",
      "description": "Courage, leadership, land/property gains",
      "planets": ["Mars"]
    },
    {
      "name": "Kemadruma Yoga",
      "type": "Malefic",
      "description": "Moon isolated. May cause hardships.",
      "planets": ["Moon"]
    }
  ]
}
```

**Yogas detected:**

| Yoga | Type | Condition |
|------|------|-----------|
| Ruchaka | Mahapurusha | Mars in kendra in own/exalted sign |
| Bhadra | Mahapurusha | Mercury in kendra in own/exalted sign |
| Hamsa | Mahapurusha | Jupiter in kendra in own/exalted sign |
| Malavya | Mahapurusha | Venus in kendra in own/exalted sign |
| Shasha | Mahapurusha | Saturn in kendra in own/exalted sign |
| Gajakesari | Benefic | Jupiter in kendra from Moon |
| Budha-Aditya | Benefic | Sun-Mercury conjunction |
| Chandra-Mangala | Mixed | Moon-Mars conjunction/opposition |
| Dhana | Benefic | 2nd/11th lord connects with 5th/9th lord |
| Kemadruma | Malefic | Moon isolated (no planets in 2nd/12th) |
| Neecha Bhanga | Benefic | Debilitation cancelled |

---

### POST `/api/v1/ashtakavarga/`

Ashtakavarga planetary strength scores using BPHS tables.

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "bhinnashtakavarga": {
    "sun": {
      "scores": [4, 5, 2, 6, 3, 2, 5, 4, 7, 4, 5, 1],
      "total": 48,
      "signs": [
        {
          "rasi": "Aries",
          "score": 4,
          "strength": "Moderate"
        }
        // ... 12 signs
      ]
    }
    // moon, mars, mercury, jupiter, venus, saturn
  },
  "sarvashtakavarga": {
    "scores": [23, 29, 21, 34, 30, 22, 25, 31, 37, 35, 32, 18],
    "total": 337,
    "signs": [ ... ]
  }
}
```

**Score interpretation:**

| Bhinnashtakavarga | Meaning |
|-------------------|---------|
| 5+ | Strong — good transit/placement |
| 3–4 | Moderate |
| 0–2 | Weak |

| Sarvashtakavarga | Meaning |
|------------------|---------|
| 30+ | Strong sign |
| 25–29 | Moderate |
| < 25 | Weak sign |

---

## Phase 4 — Compatibility

---

### POST `/api/v1/compatibility/guna/`

36-point Ashtakoot Guna matching (Kundali Milan).

**Request — requires TWO birth data sets:**
```json
{
  "boy": {
    "year": 1998, "month": 5, "day": 10,
    "hour": 10, "minute": 30,
    "latitude": 27.7172, "longitude": 85.3240,
    "utc_offset": 5.75, "house_system": "whole_sign"
  },
  "girl": {
    "year": 2000, "month": 8, "day": 15,
    "hour": 6, "minute": 0,
    "latitude": 28.6139, "longitude": 77.2090,
    "utc_offset": 5.5, "house_system": "whole_sign"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "boy_nakshatra": "Swati",
  "girl_nakshatra": "Dhanishta",
  "boy_rasi": "Libra",
  "girl_rasi": "Capricorn",
  "total_score": 22,
  "max_score": 36,
  "percentage": 61.1,
  "compatibility": "Average",
  "recommendation": "Acceptable match — consult an astrologer",
  "kootas": [
    {
      "koota": "Nadi",
      "max": 8,
      "score": 8,
      "result": "Different Nadi — full score",
      "boy_nadi": "Aadi",
      "girl_nadi": "Madhya",
      "description": "Health, progeny, and genetic compatibility. Most critical koota."
    }
    // ... 8 kootas
  ]
}
```

**The 8 Kootas:**

| Koota | Max | Tests |
|-------|-----|-------|
| Nadi | 8 | Health & progeny (most important) |
| Bhakoot | 7 | Emotional compatibility |
| Gana | 6 | Temperament |
| Graha Maitri | 5 | Mental compatibility |
| Yoni | 4 | Physical compatibility |
| Tara | 3 | Destiny & health |
| Vasya | 2 | Attraction & control |
| Varna | 1 | Spiritual compatibility |

**Score interpretation:**

| Score | Compatibility |
|-------|--------------|
| 32–36 | Excellent |
| 24–31 | Good |
| 18–23 | Average |
| < 18 | Poor |

---

### POST `/api/v1/compatibility/dosha/`

Mangal Dosha (Kuja Dosha) check for both partners.

Same request body as `/compatibility/guna/`.

**Response:**
```json
{
  "status": "success",
  "boy": {
    "has_mangal_dosha": false,
    "mars_house_lagna": 10,
    "mars_house_moon": 7,
    "mars_house_venus": 2,
    "dosha_from_lagna": false,
    "dosha_from_moon": true,
    "dosha_from_venus": true,
    "cancellations": ["Mars in own sign or exaltation — dosha cancelled"],
    "severity": "Medium",
    "mars_rasi": "Aries",
    "ascendant_rasi": "Cancer"
  },
  "girl": {
    "has_mangal_dosha": true,
    "mars_house_lagna": 1,
    "severity": "High",
    "cancellations": []
  },
  "double_dosha_cancels": false,
  "note": "Check individual dosha details above."
}
```

**Dosha houses:** Mars in 1, 2, 4, 7, 8, or 12 from Lagna = Mangal Dosha

**Severity:**
- `High` — Dosha from Lagna AND Moon
- `Medium` — Dosha from Lagna or Moon
- `None` — No dosha

**Cancellations checked:**
- Mars in own sign (Aries/Scorpio) or exaltation (Capricorn)
- Jupiter aspects Mars (5th, 7th, or 9th from Mars)
- Both partners have dosha → double dosha cancels

---

## Phase 5 — Transits

---

### POST `/api/v1/transits/current/`

All planet transits RIGHT NOW vs the natal chart.

**Request:** Standard birth data only.

**Response:**
```json
{
  "status": "success",
  "transit_time": "2026-03-14 15:05 UTC",
  "ayanamsa": "Lahiri",
  "sade_sati": {
    "natal_moon_rasi": "Libra",
    "transit_saturn_rasi": "Pisces",
    "in_sade_sati": false,
    "sade_sati_phase": null,
    "in_dhaiya": false,
    "dhaiya_type": null,
    "saturn_from_moon": 6
  },
  "moon_transit": {
    "moon_longitude": 275.703376,
    "rasi": "Capricorn",
    "nakshatra": "Uttara Ashadha",
    "nakshatra_lord": "Sun",
    "pada": 3,
    "hours_to_next_sign": 46.8,
    "next_rasi": "Aquarius"
  },
  "transits": [
    {
      "planet": "jupiter",
      "transit_rasi": "Gemini",
      "transit_house": 12,
      "longitude": 80.882069,
      "retrograde": false,
      "avarga_score": 4,
      "favorable": true,
      "effect": "Spiritual growth, foreign travel, moksha themes",
      "conjunctions": []
    }
    // ... all planets sorted by importance
  ]
}
```

**Transit fields:**

| Field | Description |
|-------|-------------|
| `transit_house` | House number from natal Ascendant (1–12) |
| `avarga_score` | Ashtakavarga score in that sign (higher = stronger) |
| `favorable` | true if avarga_score ≥ 4 |
| `effect` | Classical Jyotish interpretation |
| `conjunctions` | Natal planets within 3° orb |

**Sade Sati phases:**
- Rising (1st phase) — Saturn in 12th from natal Moon
- Peak (2nd phase) — Saturn on natal Moon sign
- Setting (3rd phase) — Saturn in 2nd from natal Moon

---

### POST `/api/v1/transits/date/`

Transits for a specific date vs natal chart.

**Additional required fields:**
```json
{
  "transit_year":   2026,
  "transit_month":  6,
  "transit_day":    15,
  "transit_hour":   12,
  "transit_minute": 0
}
```

Same response structure as `/transits/current/` but with `transit_date` instead of `transit_time`.

---

### POST `/api/v1/transits/moon/`

Current Moon transit — Chandra Gochar. No birth data needed.

**Request:** `{}` or optionally pass `transit_year`, `transit_month`, `transit_day`.

**Response:**
```json
{
  "status": "success",
  "ayanamsa": "Lahiri",
  "moon_longitude": 275.703376,
  "rasi": "Capricorn",
  "rasi_index": 9,
  "degree_in_rasi": 5.7034,
  "nakshatra": "Uttara Ashadha",
  "nakshatra_lord": "Sun",
  "pada": 3,
  "speed_deg_per_day": 12.4702,
  "degrees_to_next_sign": 24.2966,
  "hours_to_next_sign": 46.8,
  "next_rasi": "Aquarius"
}
```

> Moon changes sign approximately every 2.25 days. This is the most frequently polled endpoint for daily horoscope apps.

---

## Error Responses

All validation errors return `HTTP 400` with this structure:

```json
{
  "errors": {
    "month": ["Ensure this value is less than or equal to 12."],
    "day": ["Day 30 is invalid for month 2/1998"]
  }
}
```

Missing required field:
```json
{
  "errors": {
    "latitude": ["This field is required."]
  }
}
```

Invalid division number:
```json
{
  "errors": {
    "division": "Must be one of: 2, 3, 7, 9, 10, 12, 16, 30, 60"
  }
}
```

---

## Common Values Reference

### Rasi (Zodiac Signs)

| Index | Name | Lord |
|-------|------|------|
| 0 | Aries | Mars |
| 1 | Taurus | Venus |
| 2 | Gemini | Mercury |
| 3 | Cancer | Moon |
| 4 | Leo | Sun |
| 5 | Virgo | Mercury |
| 6 | Libra | Venus |
| 7 | Scorpio | Mars |
| 8 | Sagittarius | Jupiter |
| 9 | Capricorn | Saturn |
| 10 | Aquarius | Saturn |
| 11 | Pisces | Jupiter |

### 27 Nakshatras

| # | Name | Lord |
|---|------|------|
| 1 | Ashwini | Ketu |
| 2 | Bharani | Venus |
| 3 | Krittika | Sun |
| 4 | Rohini | Moon |
| 5 | Mrigashira | Mars |
| 6 | Ardra | Rahu |
| 7 | Punarvasu | Jupiter |
| 8 | Pushya | Saturn |
| 9 | Ashlesha | Mercury |
| 10 | Magha | Ketu |
| 11 | Purva Phalguni | Venus |
| 12 | Uttara Phalguni | Sun |
| 13 | Hasta | Moon |
| 14 | Chitra | Mars |
| 15 | Swati | Rahu |
| 16 | Vishakha | Jupiter |
| 17 | Anuradha | Saturn |
| 18 | Jyeshtha | Mercury |
| 19 | Mula | Ketu |
| 20 | Purva Ashadha | Venus |
| 21 | Uttara Ashadha | Sun |
| 22 | Shravana | Moon |
| 23 | Dhanishta | Mars |
| 24 | Shatabhisha | Rahu |
| 25 | Purva Bhadrapada | Jupiter |
| 26 | Uttara Bhadrapada | Saturn |
| 27 | Revati | Mercury |

### Vimshottari Dasha Sequence

| Planet | Years |
|--------|-------|
| Ketu | 7 |
| Venus | 20 |
| Sun | 6 |
| Moon | 10 |
| Mars | 7 |
| Rahu | 18 |
| Jupiter | 16 |
| Saturn | 19 |
| Mercury | 17 |
| **Total** | **120** |