from django.urls import path
from . import views

urlpatterns = [
    # Phase 1
    path('planets/',   views.planet_positions, name='planet-positions'),
    path('houses/',    views.ascendant_houses,  name='ascendant-houses'),
    path('chart/',     views.full_chart,         name='full-chart'),
    # Phase 2
    path('nakshatra/', views.nakshatra,          name='nakshatra'),
    path('panchang/',  views.panchang,           name='panchang'),
    path('dasha/',     views.dasha,              name='dasha'),
]