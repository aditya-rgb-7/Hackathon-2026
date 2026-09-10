"""
risk.py - Prototype Heuristic Multi-Factor Hazard Model
Not a certified geotechnical instrument; built for prototype early detection.
"""

def calculate_moisture_trend(readings):
    """
    Computes moisture change rate (% / hour) from ordered readings (newest first).
    """
    if not readings or len(readings) < 2:
        return 0.0, "Stable"

    current = readings[0]['moisture']
    previous = readings[1]['moisture']
    
    # Calculate difference
    diff = current - previous
    rate_per_hour = round(diff * 6.0, 2)  # Normalized rate for 10-minute reporting intervals

    if rate_per_hour >= 4.0:
        trend = "Rapidly Increasing"
    elif rate_per_hour > 0.5:
        trend = "Increasing"
    elif rate_per_hour < -0.5:
        trend = "Decreasing"
    else:
        trend = "Stable"

    return rate_per_hour, trend

def evaluate_hazard_risk(current_moisture, rate_per_hour, rainfall_mm, is_online=True):
    """
    Evaluates multi-factor disaster risk.
    Risk levels: SAFE, WATCH, WARNING, CRITICAL, SENSOR_OFFLINE
    """
    if not is_online:
        return {
            "level": "SENSOR_OFFLINE",
            "score": 0,
            "color": "#6c757d",
            "message": "SENSOR OFFLINE / DATA UNAVAILABLE"
        }

    score = 0

    # Moisture Level factor (0-50 pts)
    if current_moisture >= 85.0:
        score += 50
    elif current_moisture >= 70.0:
        score += 35
    elif current_moisture >= 55.0:
        score += 20
    elif current_moisture >= 40.0:
        score += 10

    # Moisture Acceleration factor (0-30 pts)
    if rate_per_hour >= 5.0:
        score += 30
    elif rate_per_hour >= 2.5:
        score += 20
    elif rate_per_hour >= 0.8:
        score += 10

    # Rainfall factor (0-20 pts)
    if rainfall_mm >= 30.0:
        score += 20
    elif rainfall_mm >= 15.0:
        score += 12
    elif rainfall_mm >= 5.0:
        score += 5

    # Determine state from cumulative composite score
    if score >= 70 or current_moisture >= 88.0:
        return {
            "level": "CRITICAL",
            "score": score,
            "color": "#d90429",
            "message": "Critical moisture saturation! High probability of slope failure or debris flow."
        }
    elif score >= 45 or current_moisture >= 65.0:
        return {
            "level": "WARNING",
            "score": score,
            "color": "#f77f00",
            "message": "Warning: High saturation & rapid accumulation. Prepare response teams."
        }
    elif score >= 25 or current_moisture >= 45.0:
        return {
            "level": "WATCH",
            "score": score,
            "color": "#fcbf49",
            "message": "Watch status: Moisture rising above baseline. Continue automated tracking."
        }
    else:
        return {
            "level": "SAFE",
            "score": score,
            "color": "#2ec4b6",
            "message": "Normal conditions: Slope pore-water pressure within baseline tolerances."
        }