def risk_level(atr, price):

    if price <= 0:
        return "Unknown"

    ratio = atr / price

    if ratio < 0.015:
        return "Low"

    elif ratio < 0.03:
        return "Medium"

    else:
        return "High"