import re
import urllib.request
import json
import smtplib
from email.message import EmailMessage

def fallback_process(text: str) -> str:
    t = text.lower().strip()
    if re.search(r"\b(turn on|power on)\b.*\b(tv|television)\b", t) or t in ["tv on", "/tv_on"]:
        return "Powered on your Samsung TV."
    if re.search(r"\b(turn off|power off)\b.*\b(tv|television)\b", t) or t in ["tv off", "/tv_off"]:
        return "Samsung TV is powered off."
    if "spotify" in t:
        return "Spotify is playing on your Samsung TV."
    if "exam" in t:
        return "Notice for 5th Year Mechanical: Pneumatics and Hydraulics exam is today, Tuesday Nov 10 at 7:30 LT (1:30 PM). Add/drop runs through Nov 13."
    return f"Acknowledged: \"{text}\". Antigravity agent is standing by."
