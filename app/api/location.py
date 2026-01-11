"""
Location API Endpoints
Provides geocoding (pincode to coordinates) and climate data for project locations.
Uses free APIs: Nominatim (OpenStreetMap) for geocoding, Open-Meteo for climate.
"""

import httpx
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta

router = APIRouter(prefix="/location", tags=["Location"])

# Cache for geocoding results to avoid repeated API calls
_geocode_cache: Dict[str, Dict] = {}
_climate_cache: Dict[str, Dict] = {}


async def geocode_pincode(pincode: str, country: str = "India") -> Optional[Dict[str, Any]]:
    """
    Convert pincode/postal code to latitude and longitude using Nominatim.
    Uses OpenStreetMap's free geocoding service.
    """
    cache_key = f"{pincode}_{country}"
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]
    
    # Nominatim API (OpenStreetMap) - free, no API key required
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "postalcode": pincode,
        "country": country,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "GLC-Platform/1.0 (Green Lending Compliance)"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                result = {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", ""),
                    "address": data[0].get("address", {}),
                    "pincode": pincode,
                    "country": country
                }
                _geocode_cache[cache_key] = result
                return result
            
            return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


async def get_climate_data(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get climate and weather data for a location using Open-Meteo API.
    Free API, no key required.
    """
    cache_key = f"{lat:.2f}_{lon:.2f}"
    if cache_key in _climate_cache:
        return _climate_cache[cache_key]
    
    # Open-Meteo API - free, no API key required
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,uv_index_max",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            # Calculate averages from daily data
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            
            avg_temp_max = sum(temps_max) / len(temps_max) if temps_max else 0
            avg_temp_min = sum(temps_min) / len(temps_min) if temps_min else 0
            total_precip = sum(precip) if precip else 0
            
            # Weather code interpretation
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current.get("weather_code", 0)
            
            result = {
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "precipitation": current.get("precipitation"),
                    "cloud_cover": current.get("cloud_cover"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "weather_code": weather_code,
                    "weather_description": weather_codes.get(weather_code, "Unknown"),
                },
                "forecast_7day": {
                    "avg_temp_max": round(avg_temp_max, 1),
                    "avg_temp_min": round(avg_temp_min, 1),
                    "total_precipitation": round(total_precip, 1),
                    "dates": daily.get("time", []),
                    "temps_max": temps_max,
                    "temps_min": temps_min,
                    "precipitation": precip,
                    "uv_index": daily.get("uv_index_max", [])
                },
                "timezone": data.get("timezone"),
                "elevation": data.get("elevation"),
            }
            
            _climate_cache[cache_key] = result
            return result
    except Exception as e:
        print(f"Climate data error: {e}")
        return None


def assess_environmental_risk(climate_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
    """
    Assess environmental risks based on climate data and location.
    """
    risks = []
    risk_level = "low"
    
    if not climate_data:
        return {"risk_level": "unknown", "risks": [], "recommendations": []}
    
    current = climate_data.get("current", {})
    forecast = climate_data.get("forecast_7day", {})
    
    # Temperature risk
    avg_max = forecast.get("avg_temp_max", 25)
    if avg_max > 40:
        risks.append("Extreme heat risk - may affect project operations")
        risk_level = "high"
    elif avg_max > 35:
        risks.append("High temperature conditions")
        risk_level = "medium" if risk_level == "low" else risk_level
    
    # Precipitation/flood risk
    total_precip = forecast.get("total_precipitation", 0)
    if total_precip > 100:
        risks.append("High precipitation - potential flood risk")
        risk_level = "high"
    elif total_precip > 50:
        risks.append("Moderate precipitation expected")
        risk_level = "medium" if risk_level == "low" else risk_level
    
    # UV risk
    uv_indices = forecast.get("uv_index", [])
    max_uv = max(uv_indices) if uv_indices else 0
    if max_uv > 10:
        risks.append("Extreme UV exposure risk")
    elif max_uv > 7:
        risks.append("High UV index")
    
    # Humidity assessment
    humidity = current.get("humidity", 50)
    if humidity > 85:
        risks.append("High humidity - may affect equipment and materials")
    
    # Generate recommendations
    recommendations = []
    if "flood" in str(risks).lower():
        recommendations.append("Consider flood mitigation measures in project design")
    if "heat" in str(risks).lower():
        recommendations.append("Plan for heat management and worker safety protocols")
    if "UV" in str(risks).lower():
        recommendations.append("Implement UV protection measures for outdoor work")
    
    if not risks:
        risks.append("No significant environmental risks identified")
        recommendations.append("Standard environmental monitoring recommended")
    
    return {
        "risk_level": risk_level,
        "risks": risks,
        "recommendations": recommendations,
        "climate_zone": determine_climate_zone(avg_max, total_precip)
    }


def determine_climate_zone(avg_temp: float, precipitation: float) -> str:
    """Determine climate zone based on temperature and precipitation."""
    if avg_temp > 30 and precipitation < 20:
        return "Hot Arid"
    elif avg_temp > 30 and precipitation > 50:
        return "Tropical"
    elif avg_temp > 20 and precipitation > 30:
        return "Subtropical"
    elif avg_temp > 10 and precipitation > 20:
        return "Temperate"
    elif avg_temp < 10:
        return "Cold"
    else:
        return "Semi-Arid"


@router.get("/geocode")
async def geocode_location(
    pincode: str = Query(..., description="Postal code / PIN code"),
    country: str = Query("India", description="Country name")
):
    """
    Convert pincode/postal code to geographic coordinates.
    Uses OpenStreetMap Nominatim (free, no API key).
    """
    result = await geocode_pincode(pincode, country)
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"Could not find location for pincode: {pincode}"
        )
    
    return result


@router.get("/climate")
async def get_location_climate(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get climate and weather data for coordinates.
    Uses Open-Meteo API (free, no API key).
    """
    climate = await get_climate_data(lat, lon)
    
    if not climate:
        raise HTTPException(
            status_code=500,
            detail="Could not fetch climate data"
        )
    
    # Add environmental risk assessment
    climate["environmental_risk"] = assess_environmental_risk(climate, lat, lon)
    
    return climate


@router.get("/full/{pincode}")
async def get_full_location_data(
    pincode: str,
    country: str = Query("India", description="Country name")
):
    """
    Get complete location data: coordinates + climate + environmental risk.
    Single endpoint for all location-related data.
    """
    # Step 1: Geocode pincode
    geo = await geocode_pincode(pincode, country)
    
    if not geo:
        # Return default coordinates for India if geocoding fails
        geo = {
            "lat": 20.5937,
            "lon": 78.9629,
            "display_name": f"India (pincode: {pincode})",
            "pincode": pincode,
            "country": country,
            "geocode_failed": True
        }
    
    # Step 2: Get climate data
    climate = await get_climate_data(geo["lat"], geo["lon"])
    
    # Step 3: Assess environmental risk
    env_risk = assess_environmental_risk(climate, geo["lat"], geo["lon"]) if climate else None
    
    return {
        "location": geo,
        "climate": climate,
        "environmental_risk": env_risk
    }
