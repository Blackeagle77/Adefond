# main.py
# Analyse fondamentale quotidienne avec API Myfxbook
# Actifs : BTC/USD, GBP/JPY, XAU/USD

import requests
import datetime
import os

# Récupérer les identifiants depuis les secrets GitHub
MYFXBOOK_EMAIL = os.getenv("MYFXBOOK_EMAIL")
MYFXBOOK_PASSWORD = os.getenv("MYFXBOOK_PASSWORD")

def login():
    url = "https://www.myfxbook.com/api/login.json"
    params = {"email": MYFXBOOK_EMAIL, "password": MYFXBOOK_PASSWORD}
    r = requests.get(url, params=params)
    data = r.json()
    if data["error"]:
        raise Exception("Erreur login Myfxbook: " + data["message"])
    return data["session"]

def logout(session):
    url = "https://www.myfxbook.com/api/logout.json"
    requests.get(url, params={"session": session})

def fetch_prices(session):
    url = "https://www.myfxbook.com/api/get-market.json"
    r = requests.get(url, params={"session": session})
    data = r.json()
    prices = {}
    for item in data["symbols"]:
        if item["name"] in ["BTCUSD", "GBPJPY", "XAUUSD"]:
            prices[item["name"]] = item["bid"]
    return prices

def fetch_events(session):
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    r = requests.get(url, params={"session": session})
    data = r.json()
    today = datetime.date.today().isoformat()
    events = [ev for ev in data["calendar"] if ev["date"].startswith(today)]
    return events

def fetch_news(session):
    url = "https://www.myfxbook.com/api/get-community-outlook.json"
    r = requests.get(url, params={"session": session})
    data = r.json()
    return data["symbols"]

def analyze_asset(symbol, price, events, news):
    score = 0
    drivers = []

    # Exemple simplifié : inflation US pèse sur BTC et Gold
    for ev in events:
        if symbol == "BTCUSD" and ev["country"] == "US" and "CPI" in ev["title"]:
            if ev["actual"] > ev["forecast"]:
                score -= 0.5
                drivers.append("Inflation US plus forte → pression sur BTC")
        if symbol == "GBPJPY" and ev["country"] == "UK" and "Retail" in ev["title"]:
            if ev["actual"] > ev["forecast"]:
                score += 0.5
                drivers.append("Ventes UK meilleures → GBP soutenu")
        if symbol == "XAUUSD" and ev["country"] == "US" and "CPI" in ev["title"]:
            if ev["actual"] > ev["forecast"]:
                score -= 0.3
                drivers.append("Inflation US → USD fort → Gold sous pression")

    # Sentiment communautaire
    for nw in news:
        if nw["name"] == symbol:
            if nw["longPercentage"] > nw["shortPercentage"]:
                score += 0.2
                drivers.append("Sentiment haussier de la communauté")
            else:
                score -= 0.2
                drivers.append("Sentiment baissier de la communauté")

    if score > 0.3:
        sentiment = "Haussier"
    elif score < -0.3:
        sentiment = "Baissier"
    else:
        sentiment = "Neutre"

    return {
        "symbol": symbol,
        "price": price,
        "score": score,
        "sentiment": sentiment,
        "drivers": drivers
    }

def generate_report():
    today = datetime.date.today()
    session = login()

    prices = fetch_prices(session)
    events = fetch_events(session)
    news = fetch_news(session)

    report_lines = [f"Rapport fondamental quotidien – {today}\n"]

    for sym in ["BTCUSD", "GBPJPY", "XAUUSD"]:
        analysis = analyze_asset(sym, prices[sym], events, news)
        report_lines.append(f"Actif: {analysis['symbol']}")
        report_lines.append(f"Prix actuel: {analysis['price']}")
        report_lines.append(f"Sentiment: {analysis['sentiment']} (score: {analysis['score']})")
        report_lines.append("Facteurs clés:")
        for d in analysis["drivers"]:
            report_lines.append(f"  - {d}")
        report_lines.append("")

    report = "\n".join(report_lines)
    filename = f"rapport_{today}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    logout(session)

if __name__ == "__main__":
    generate_report()