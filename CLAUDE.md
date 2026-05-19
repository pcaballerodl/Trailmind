# TrailMind — Planificador de Expediciones de Montaña

## Descripción
Web app para montañeros avanzados que analiza tracks GPX y genera
planes de expedición inteligentes con horarios, campamentos, gestión
de material y dieta. Usa IA (Claude) como cerebro central.

## Stack técnico
- Backend: Python + Flask
- Frontend: HTML + CSS + JavaScript (sin frameworks)
- Mapas: Leaflet.js + OpenStreetMap
- Gráficos: Chart.js
- IA: Claude API (anthropic)
- APIs externas: Open-Meteo (meteorología), Overpass (OSM)
- Parser GPX: gpxpy

## Estructura del proyecto
- src/          → código fuente
- src/main.py   → entrada principal Flask
- src/gpx/      → parser y análisis de tracks
- src/weather/  → integración Open-Meteo
- src/ai/       → integración Claude API
- src/static/   → HTML, CSS, JS del frontend
- tests/        → tests por módulo

## Reglas generales
- Todo el código en español (comentarios y variables)
- Cada módulo en su carpeta correspondiente
- Variables de entorno en .env, nunca hardcodeadas
- Commits semánticos: feat:, fix:, test:, docs:
- Docker debe funcionar en todo momento

## Variables de entorno necesarias
ANTHROPIC_API_KEY=
