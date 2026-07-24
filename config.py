# AI 股票評分等級

def get_rating(score):

    if score >= 90:
        return "A+", "★★★★★", "Strong Buy"

    elif score >= 80:
        return "A", "★★★★☆", "Buy"

    elif score >= 65:
        return "B+", "★★★★☆", "Moderate Buy"

    elif score >= 55:
        return "B", "★★★☆☆", "Hold"

    elif score >= 45:
        return "C", "★★☆☆☆", "Reduce"

    elif score >= 30:
        return "D", "★☆☆☆☆", "Sell"

    else:
        return "F", "☆☆☆☆☆", "Strong Sell"