"""
Environmental & Sustainability Data API
Provides climate data and air quality information for project locations.
Uses Open-Meteo APIs (free, no API key required).
"""

import httpx
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

router = APIRouter(prefix="/environment", tags=["Environment"])

# Cache for API results
_climate_cache: Dict[str, Dict] = {}
_air_quality_cache: Dict[str, Dict] = {}


async def get_climate_data(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get current climate data using Open-Meteo Climate API.
    """
    cache_key = f"climate_{lat:.2f}_{lon:.2f}"
    if cache_key in _climate_cache:
        return _climate_cache[cache_key]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m", 
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "uv_index_max",
            "wind_speed_10m_max"
        ],
        "timezone": "auto",
        "forecast_days": 1
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            # Weather code interpretation
            weather_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current.get("weather_code", 0)
            
            result = {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "cloud_cover": current.get("cloud_cover"),
                "pressure": current.get("pressure_msl"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "weather_code": weather_code,
                "weather_description": weather_codes.get(weather_code, "Unknown"),
                "temp_max": daily.get("temperature_2m_max", [None])[0],
                "temp_min": daily.get("temperature_2m_min", [None])[0],
                "uv_index": daily.get("uv_index_max", [None])[0],
                "wind_max": daily.get("wind_speed_10m_max", [None])[0],
                "precipitation_daily": daily.get("precipitation_sum", [None])[0],
                "timezone": data.get("timezone"),
                "elevation": data.get("elevation"),
            }
            
            _climate_cache[cache_key] = result
            return result
    except Exception as e:
        print(f"Climate data error: {e}")
        return None


async def get_air_quality_data(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get current air quality data using Open-Meteo Air Quality API.
    """
    cache_key = f"air_{lat:.2f}_{lon:.2f}"
    if cache_key in _air_quality_cache:
        return _air_quality_cache[cache_key]
    
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "aerosol_optical_depth",
            "dust",
            "uv_index",
            "uv_index_clear_sky",
            "ammonia"
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            
            # Calculate AQI category based on PM2.5
            pm25 = current.get("pm2_5", 0) or 0
            if pm25 <= 12:
                aqi_category = "Good"
                aqi_color = "green"
            elif pm25 <= 35.4:
                aqi_category = "Moderate"
                aqi_color = "yellow"
            elif pm25 <= 55.4:
                aqi_category = "Unhealthy for Sensitive"
                aqi_color = "orange"
            elif pm25 <= 150.4:
                aqi_category = "Unhealthy"
                aqi_color = "red"
            elif pm25 <= 250.4:
                aqi_category = "Very Unhealthy"
                aqi_color = "purple"
            else:
                aqi_category = "Hazardous"
                aqi_color = "maroon"
            
            result = {
                "pm10": round(current.get("pm10", 0) or 0, 1),
                "pm2_5": round(current.get("pm2_5", 0) or 0, 1),
                "carbon_monoxide": round(current.get("carbon_monoxide", 0) or 0, 1),
                "nitrogen_dioxide": round(current.get("nitrogen_dioxide", 0) or 0, 1),
                "sulphur_dioxide": round(current.get("sulphur_dioxide", 0) or 0, 1),
                "ozone": round(current.get("ozone", 0) or 0, 1),
                "aerosol_optical_depth": round(current.get("aerosol_optical_depth", 0) or 0, 3),
                "dust": round(current.get("dust", 0) or 0, 1),
                "uv_index": round(current.get("uv_index", 0) or 0, 1),
                "uv_index_clear_sky": round(current.get("uv_index_clear_sky", 0) or 0, 1),
                "ammonia": round(current.get("ammonia", 0) or 0, 1),
                "aqi_category": aqi_category,
                "aqi_color": aqi_color
            }
            
            _air_quality_cache[cache_key] = result
            return result
    except Exception as e:
        print(f"Air quality data error: {e}")
        return None


@router.get("/data")
async def get_environmental_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get complete environmental data: climate + air quality.
    """
    climate = await get_climate_data(lat, lon)
    air_quality = await get_air_quality_data(lat, lon)
    
    if not climate and not air_quality:
        raise HTTPException(
            status_code=500,
            detail="Could not fetch environmental data"
        )
    
    return {
        "climate": climate,
        "air_quality": air_quality,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
