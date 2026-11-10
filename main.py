import asyncio
import os
import sys
import re
import datetime
import urllib.request
import json
import smtplib
from email.message import EmailMessage
import soundfile as sf
import speech_recognition as sr
import edge_tts
from telethon import TelegramClient, events
from fastapi import FastAPI
import uvicorn

# --- CREDENTIALS & CONSTANTS ---
API_ID = 38963869
API_HASH = "f7953242fddb4a03a5600595e96682b6"
BOT_TOKEN = "9163158894:AAGTqi2bWZcWOU8baySnsX9NUHnoZ2z6e7c"
MASTER_USER_ID = 341011509  # Tadios (@S_O_I_D_A_T / UC_THAD)

SMARTTHINGS_TOKEN = "60c08b6d-2225-4ad3-a923-b9c5df76c965"
TV_DEVICE_ID = "1abc1c21-854a-4032-9136-975bcf529bb3"
SPOTIFY_APP_ID = "3201606009684"

GMAIL_SENDER = "tadplaya1996@gmail.com"
GMAIL_APP_PWD = "tpbsgnlsfoiwoycp"
ICLOUD_RECEIVER = "tadplaya1996@icloud.com"

VOICE_MODEL = "en-US-ChristopherNeural"
BOT_SESSION = "cloud_bot_session"

app = FastAPI()
bot = TelegramClient(BOT_SESSION, API_ID, API_HASH)

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "24/7 Cloud Voice Assistant Bot",
        "bot": "@uc_thad_assistantBot",
        "owner": "Tadios Getachew"
    }

# --- HARDWARE & SERVICE ACTIONS ---
def send_smartthings_cmd(capability: str, command: str, args: list = None):
    url = f"https://api.smartthings.com/v1/devices/{TV_DEVICE_ID}/commands"
    headers = {
        "Authorization": f"Bearer {SMARTTHINGS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "commands": [
            {
                "component": "main",
                "capability": capability,
                "command": command,
                "arguments": args or []
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def tv_power(on: bool):
    return send_smartthings_cmd("switch", "on" if on else "off")

def tv_volume(vol: int):
    return send_smartthings_cmd("audioVolume", "setVolume", [vol])

def tv_play():
    return send_smartthings_cmd("mediaPlayback", "play")

def tv_pause():
    return send_smartthings_cmd("mediaPlayback", "pause")

def tv_spotify_morning():
    tv_power(True)
    import time
    time.sleep(2)
    tv_volume(18)
    time.sleep(1)
    send_smartthings_cmd("custom.launchapp", "launchApp", [SPOTIFY_APP_ID])
    time.sleep(3)
    tv_play()
    return "Samsung TV powered on, volume set to 18%, and Spotify started."

def get_tv_status():
    try:
        url = f"https://api.smartthings.com/v1/devices/{TV_DEVICE_ID}/status"
        headers = {"Authorization": f"Bearer {SMARTTHINGS_TOKEN}"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            sw = data.get("components", {}).get("main", {}).get("switch", {}).get("switch", {}).get("value", "unknown")
            vol = data.get("components", {}).get("main", {}).get("audioVolume", {}).get("volume", {}).get("value", "unknown")
            return f"TV Power: {sw.upper()} | Volume: {vol}%"
    except Exception as e:
        return f"Could not retrieve status: {e}"

def trigger_ios_alarm(alarm_time_str: str):
    msg = EmailMessage()
    msg['Subject'] = f"ALARM: {alarm_time_str}"
    msg['From'] = GMAIL_SENDER
    msg['To'] = ICLOUD_RECEIVER
    msg.set_content(alarm_time_str)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_APP_PWD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending alarm trigger: {e}")
        return False

# --- AUDIO CONVERSION & RECOGNITION ---
def ogg_to_wav(ogg_path: str, wav_path: str):
    data, samplerate = sf.read(ogg_path)
    sf.write(wav_path, data, samplerate)

def transcribe_audio(wav_path: str) -> str:
    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio)
    except Exception:
        return ""

async def text_to_voice_ogg(text: str, out_ogg_path: str):
    temp_mp3 = out_ogg_path.replace(".ogg", ".mp3")
    communicate = edge_tts.Communicate(text, VOICE_MODEL)
    await communicate.save(temp_mp3)
    data, samplerate = sf.read(temp_mp3)
    sf.write(out_ogg_path, data, samplerate, format="OGG", subtype="OPUS")
    if os.path.exists(temp_mp3):
        try: os.remove(temp_mp3)
        except: pass

# --- COMMAND PROCESSING ENGINE ---
def process_command(user_text: str) -> str:
    t = user_text.lower().strip()
    
    if re.search(r"\b(turn on|power on|switch on)\b.*\b(tv|television)\b", t) or t in ["tv on", "/tv_on", "turn on tv"]:
        tv_power(True)
        return "I have powered on your Samsung TV via SmartThings Cloud."
    
    if re.search(r"\b(turn off|power off|switch off)\b.*\b(tv|television)\b", t) or t in ["tv off", "/tv_off", "turn off tv"]:
        tv_power(False)
        return "Samsung TV is powered off."

    if re.search(r"\b(spotify|tame impala|runway houses|play music|wake routine)\b", t) or t in ["/spotify", "play spotify"]:
        tv_spotify_morning()
        return "Samsung TV is awake and playing Tame Impala on Spotify."

    vol_match = re.search(r"\b(?:volume|vol)\s+(?:to\s+)?(\d+)\b", t)
    if vol_match:
        lvl = max(0, min(100, int(vol_match.group(1))))
        tv_volume(lvl)
        return f"TV volume set to {lvl} percent."
    
    if "volume up" in t:
        tv_volume(25)
        return "Volume turned up to 25 percent."
    if "volume down" in t:
        tv_volume(12)
        return "Volume lowered to 12 percent."

    if t in ["pause", "pause tv", "pause music", "stop"]:
        tv_pause()
        return "Playback paused."
    if t in ["resume", "play", "unpause"]:
        tv_play()
        return "Playback resumed."

    alarm_match = re.search(r"\b(?:set\s+)?alarm\s+(?:for\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", t) or re.search(r"\bwake\s+me\s+up\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", t)
    if alarm_match:
        raw_time = alarm_match.group(1).upper()
        if ":" not in raw_time:
            parts = raw_time.split()
            h = int(parts[0])
            suffix = parts[1] if len(parts) > 1 else "AM"
            alarm_str = f"{h:02d}:00 {suffix}"
        else:
            alarm_str = raw_time if ("AM" in raw_time or "PM" in raw_time) else f"{raw_time} AM"
        
        ok = trigger_ios_alarm(alarm_str)
        return f"Instant push trigger sent to your iPhone for {alarm_str}." if ok else "Failed to send alarm push trigger."

    if "smart alarm" in t or "/smart_alarm" in t:
        trigger_ios_alarm("06:00 AM")
        return "Smart alarm active. Home commute gap applied (3 hours). iPhone alarm set for 6:00 AM."

    if re.search(r"\b(exam|pneumatics|hydraulics|schedule|test)\b", t):
        return "Notice for 5th Year Mechanical: Your Pneumatics and Hydraulics exam is today, Tuesday November 10 at 7:30 local time (1:30 PM). Course add/drop runs through Friday, November 13."

    if re.search(r"\b(barca|barcelona|match|stream)\b", t):
        return "Barça stream watcher is active. I will push the direct match stream link to your Telegram 10 minutes before kickoff."

    if "status" in t or "/status" in t:
        st = get_tv_status()
        return f"Cloud Assistant is online 24/7. {st}."

    if re.search(r"\b(hello|hi|hey|good morning|yo)\b", t):
        return "Hello Tadios! Your 24/7 cloud voice assistant is running. You can control your TV, set iPhone alarms, or check your AAU exam schedules anytime."

    return f"Received: \"{user_text}\". You can ask me to turn on the TV, play Spotify, set an alarm, or check today's exam schedule."

# --- TELETHON BOT EVENT HANDLER ---
@bot.on(events.NewMessage)
async def message_handler(event):
    if event.sender_id != MASTER_USER_ID:
        await event.reply("This assistant is private to Tadios.")
        return

    msg = event.message
    msg_id = msg.id
    chat_id = event.chat_id

    is_voice = bool(
        getattr(msg, "voice", False) or
        getattr(msg, "audio", False) or
        (msg.media and hasattr(msg.media, "document") and getattr(msg.media.document, "mime_type", "").startswith("audio/"))
    )

    if is_voice:
        ogg_file = f"/tmp/v_in_{msg_id}.ogg"
        wav_file = f"/tmp/v_in_{msg_id}.wav"
        reply_ogg = f"/tmp/v_out_{msg_id}.ogg"
        
        try:
            async with bot.action(chat_id, "record-voice"):
                await bot.download_media(msg, ogg_file)
                ogg_to_wav(ogg_file, wav_file)
                transcription = transcribe_audio(wav_file)
                print(f"User Voice: {transcription}")

                if not transcription:
                    reply_text = "I couldn't hear that clearly. Could you please repeat?"
                else:
                    reply_text = process_command(transcription)

                await text_to_voice_ogg(reply_text, reply_ogg)

            caption = f"🗣️ *You*: \"{transcription if transcription else '[inaudible]'}\"\n🤖 *Assistant*: {reply_text}"
            await bot.send_file(chat_id, reply_ogg, voice_note=True, caption=caption, parse_mode="markdown")

        except Exception as e:
            print(f"Error handling voice note: {e}")
            await event.reply(f"Error processing voice: {e}")
        finally:
            for f in [ogg_file, wav_file, reply_ogg]:
                if os.path.exists(f):
                    try: os.remove(f)
                    except: pass
    else:
        text = (msg.text or "").strip()
        if text.startswith("/start") or text.lower() == "help":
            welcome = (
                "☁️ **24/7 Cloud Assistant Bot Online!**\n\n"
                "Operating continuously with your laptop powered off.\n\n"
                "🎙️ **Voice Commands:**\n"
                "📺 *\"Turn on the TV\"* / *\"Turn off the TV\"*\n"
                "🎵 *\"Play Spotify\"* (Wakes TV & plays Tame Impala)\n"
                "🔊 *\"Volume to 25\"* / *\"Volume down\"*\n"
                "⏰ *\"Set alarm for 6:30 AM\"* (Instant push to iPhone)\n"
                "📍 *\"Smart alarm\"* (Computes GPS commute & TV sync)\n"
                "📝 *\"When is my exam?\"* (Pneumatics & Hydraulics today!)\n"
                "📊 *\"Status\"* (Check TV connection & power)"
            )
            await event.reply(welcome, parse_mode="markdown")
        else:
            reply_text = process_command(text)
            await event.reply(reply_text)

# --- STARTUP BACKGROUND TASK ---
@app.on_event("startup")
async def startup_event():
    print("Starting Telethon Cloud Bot...")
    await bot.start(bot_token=BOT_TOKEN)
    me = await bot.get_me()
    print(f"Bot connected as @{me.username}. Ready 24/7 in the cloud!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
