# AstroGyan API

A production-ready **Vedic Astrology REST API** built with Django, PySwissEph, and PyJHora.

Provides 19 endpoints covering everything from basic birth charts to advanced compatibility matching and transit predictions — all calculated using the **Lahiri ayanamsa (sidereal)** system.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 6 + Django REST Framework |
| Astronomy engine | PySwissEph (Swiss Ephemeris) |
| Jyotish logic | PyJHora |
| Database | MySQL |
| Ayanamsa | Lahiri (standard Vedic) |
| Language | Python 3.13 |

---

## Features

- **Birth Chart** — Planet positions, Ascendant, 12 houses (Whole Sign, Placidus, Equal, Koch)
- **Panchang** — Tithi, Vara, Nakshatra, Yoga, Karana
- **Dasha System** — Vimshottari Mahadasha + Antardasha (81 sub-periods)
- **Divisional Charts** — D2, D3, D7, D9, D10, D12, D16, D30, D60
- **Yogas** — Pancha Mahapurusha, Gajakesari, Dhana, Kemadruma, Neecha Bhanga
- **Ashtakavarga** — Full BPHS tables, Bhinnashtakavarga + Sarvashtakavarga
- **Kundali Milan** — 36-point Ashtakoot Guna matching + Mangal Dosha
- **Gochar (Transits)** — Current/date-specific transits, Sade Sati, Chandra Gochar

---

## Installation

### Prerequisites

- Python 3.11+
- MySQL 8+
- pipenv

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/astrogyan.git
cd astrogyan

# Install dependencies
pipenv install

# Activate virtual environment
pipenv shell

# Install Python packages
pip install django djangorestframework mysqlclient pyswisseph pyjhora \
    geocoder ephem pandas numpy pytz requests timezonefinder \
    geopy Pillow matplotlib scipy shapely
```

### Ephemeris Files

Download these 3 files from the [Swiss Ephemeris GitHub](https://github.com/aloistr/swisseph/tree/master/ephe) and place them in an `ephemeris/` folder at the project root:

```
astrogyan/
├── ephemeris/
│   ├── sepl_18.se1    ← Planets (1800–2400 CE)
│   ├── semo_18.se1    ← Moon
│   └── seas_18.se1    ← Asteroids
```

### Database

Create a MySQL database and update `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'astrogyan',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

Also set the ephemeris path in `settings.py`:

```python
EPHE_PATH = BASE_DIR / 'ephemeris'
```

### Run

```bash
python manage.py migrate
python manage.py runserver
```

---

## Project Structure

```
astrogyan/
├── config/
│   ├── settings.py
│   └── urls.py
├── core/
│   ├── api/
│   │   ├── urls.py          ← API routes
│   │   ├── views.py         ← Endpoint handlers
│   │   └── serializers.py   ← Input validation
│   └── astro/
│       └── calculator.py    ← All calculation logic
├── ephemeris/               ← Swiss Ephemeris .se1 files
└── manage.py
```

---

## API Overview

All endpoints:
- Accept `POST` requests with `Content-Type: application/json`
- Use **Lahiri ayanamsa** (sidereal)
- Return JSON responses

### Standard Birth Data Input

All chart endpoints accept this base request body:

```json
{
  "year":       1998,
  "month":      5,
  "day":        10,
  "hour":       10,
  "minute":     30,
  "latitude":   27.7172,
  "longitude":  85.3240,
  "utc_offset": 5.75,
  "house_system": "whole_sign"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `year` | int | Birth year (1800–2100) |
| `month` | int | Birth month (1–12) |
| `day` | int | Birth day (1–31) |
| `hour` | int | Birth hour in local time (0–23) |
| `minute` | int | Birth minute (0–59) |
| `latitude` | float | Birth location latitude (-90 to 90) |
| `longitude` | float | Birth location longitude (-180 to 180) |
| `utc_offset` | float | UTC offset (e.g. 5.75 for Nepal NPT, 5.5 for India IST) |
| `house_system` | string | `whole_sign` (default), `placidus`, `equal`, `koch` |

---

## Endpoints

### Phase 1 — Birth Chart

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chart/` | Full chart — planets + houses combined |
| POST | `/api/v1/planets/` | Planet positions only |
| POST | `/api/v1/houses/` | Ascendant + 12 houses only |

### Phase 2 — Panchang & Dasha

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/nakshatra/` | Moon's Nakshatra, Pada, lord |
| POST | `/api/v1/panchang/` | Tithi, Vara, Nakshatra, Yoga, Karana |
| POST | `/api/v1/dasha/` | Vimshottari Mahadasha (120 years) |

### Phase 3 — Advanced Charts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/antardasha/` | Mahadasha + nested Antardasha (81 periods) |
| POST | `/api/v1/divisional/` | Divisional charts (D2/D3/D7/D9/D10/D12/D16/D30/D60) |
| POST | `/api/v1/yogas/` | Vedic Yoga detection |
| POST | `/api/v1/ashtakavarga/` | Ashtakavarga scores (BPHS tables) |

### Phase 4 — Compatibility

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/compatibility/guna/` | 36-point Ashtakoot Guna Milan |
| POST | `/api/v1/compatibility/dosha/` | Mangal Dosha check for both partners |

### Phase 5 — Transits (Gochar)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/transits/current/` | Current planet transits vs natal chart |
| POST | `/api/v1/transits/date/` | Transits for a specific date |
| POST | `/api/v1/transits/moon/` | Current Moon transit (Chandra Gochar) |

---

## Quick Examples

### Full Birth Chart
```bash
curl -X POST http://localhost:8000/api/v1/chart/ \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1998, "month": 5, "day": 10,
    "hour": 10, "minute": 30,
    "latitude": 27.7172, "longitude": 85.3240,
    "utc_offset": 5.75, "house_system": "whole_sign"
  }'
```

### Kundali Milan
```bash
curl -X POST http://localhost:8000/api/v1/compatibility/guna/ \
  -H "Content-Type: application/json" \
  -d '{
    "boy":  {"year":1998,"month":5,"day":10,"hour":10,"minute":30,"latitude":27.7172,"longitude":85.3240,"utc_offset":5.75,"house_system":"whole_sign"},
    "girl": {"year":2000,"month":8,"day":15,"hour":6,"minute":0,"latitude":28.6139,"longitude":77.2090,"utc_offset":5.5,"house_system":"whole_sign"}
  }'
```

### Current Transits
```bash
curl -X POST http://localhost:8000/api/v1/transits/current/ \
  -H "Content-Type: application/json" \
  -d '{"year":1998,"month":5,"day":10,"hour":10,"minute":30,"latitude":27.7172,"longitude":85.3240,"utc_offset":5.75,"house_system":"whole_sign"}'
```

---

## License

This project uses **Swiss Ephemeris** under the GPL license.
Under GPL, this project must remain **open source**.

Credits:
- [Astrodienst AG](https://www.astro.com) — Swiss Ephemeris
- [PyJHora](https://github.com/naturalvision/pyjhora) — Jyotish calculations

---

## Roadmap

- [ ] Authentication + API key system
- [ ] User birth chart storage
- [ ] Pratyantardasha (3rd level dasha)
- [ ] Shadbala (planetary strength scores)
- [ ] Muhurta (auspicious timing)
- [ ] Production deployment guide