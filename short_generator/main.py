import os
import re
import requests
import random
import string
import numpy as np
import pandas as pd
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip

# --------- SETTINGS ---------
OUTPUT_DIR = "shorts_output"
LOG_FILE = "shorts_log.xlsx"
FONT_PATH = "fonts/Dosis-ExtraBold.ttf"  # Make sure this font exists
IMAGE_SIZE = (1080, 1920)
FONT_SIZE = 60
# ----------------------------

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------- CONTENT FETCHERS ---------
def get_chucknorris_fact():
    return requests.get("https://api.chucknorris.io/jokes/random").json()["value"]

def get_quote():
    return requests.get("https://zenquotes.io/api/random").json()[0]["q"]

def get_advice():
    return requests.get("https://api.adviceslip.com/advice").json()["slip"]["advice"]

def fetch_content(content_type: str) -> str:
    if content_type == "chucknorris":
        return get_chucknorris_fact()
    elif content_type == "quotes":
        return get_quote()
    elif content_type == "advice":
        return get_advice()
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

# --------- UTILITY FUNCTIONS ---------
def create_gradient_image(size=(1080, 1920)):
    color1 = tuple(random.randint(0, 255) for _ in range(3))
    color2 = tuple(random.randint(0, 255) for _ in range(3))
    gradient = np.zeros((size[1], size[0], 3), dtype=np.uint8)

    for y in range(size[1]):
        ratio = y / size[1]
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        gradient[y, :, :] = [r, g, b]

    return Image.fromarray(gradient)

def create_text_image(text, size=(1080, 1920), fontsize=60):
    image = create_gradient_image(size)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, fontsize)

    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w < size[0] - 100:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    total_height = len(lines) * (fontsize + 10)
    y = (size[1] - total_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((size[0] - w) // 2, y), line, font=font, fill="white")
        y += fontsize + 10

    return np.array(image)

def sanitize_filename(text, max_length=50):
    filename = re.sub(r'[^\w\s-]', '', text)
    filename = re.sub(r'[\s]+', '_', filename)
    return filename[:max_length].strip("_").lower()

def generate_id(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_next_doc_number(content_type_code):
    if os.path.exists(LOG_FILE):
        df = pd.read_excel(LOG_FILE)
        matching = df[df["Doc Number"].str.startswith(content_type_code)]
        if not matching.empty:
            last_number = max([int(x[len(content_type_code):]) for x in matching["Doc Number"]])
        else:
            last_number = 0
    else:
        df = pd.DataFrame(columns=["Doc Number", "Content Type", "Text", "Filename"])
        last_number = 0
    next_number = last_number + 1
    return df, f"{content_type_code}{str(next_number).zfill(3)}"

# --------- MAIN SHORT CREATION ---------
def create_short(text, content_type, content_type_code):
    df, doc_number = get_next_doc_number(content_type_code)

    print(f"📝 Generating TTS and video for {doc_number}: {text}")

    # Create TTS
    tts = gTTS(text=text, lang='en')
    audio_path = os.path.join(OUTPUT_DIR, f"tts_{doc_number}.mp3")
    tts.save(audio_path)

    # Create image and video
    frame = create_text_image(text, IMAGE_SIZE, FONT_SIZE)
    clip = ImageClip(frame)
    audio_clip = AudioFileClip(audio_path)
    clip = clip.set_audio(audio_clip).set_duration(audio_clip.duration)

    safe_text = sanitize_filename(text)
    video_id = generate_id()
    filename = f"{doc_number}_{safe_text}_{video_id}.mp4"
    video_path = os.path.join(OUTPUT_DIR, filename)

    clip.write_videofile(video_path, fps=30, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    print(f"✅ Saved: {video_path}")

    os.remove(audio_path)

    # Append to log
    new_row = {"Doc Number": doc_number, "Content Type": content_type, "Text": text, "Filename": filename}
    df = df._append(new_row, ignore_index=True)
    df.to_excel(LOG_FILE, index=False)

# --------- TEXTUAL MENU ---------
def main():
    print("🎬 Shorts Generator")
    print("1. Chuck Norris")
    print("2. Quotes")
    print("3. Advice")
    print("4. Random each video")

    choice = input("Choose content type (1-4): ").strip()
    count = int(input("How many videos?: ").strip())

    type_map = {
        "1": ("chucknorris", "CH"),
        "2": ("quotes", "QT"),
        "3": ("advice", "AD"),
        "4": ("random", "RAN")
    }

    if choice not in type_map:
        print("❌ Invalid option")
        return

    selected_type, selected_code = type_map[choice]
    valid_types = [("chucknorris", "CH"), ("quotes", "QT"), ("advice", "AD")]

    for i in range(count):
        if selected_type == "random":
            content_type, content_code = random.choice(valid_types)
        else:
            content_type, content_code = selected_type, selected_code

        print(f"\n⏳ Generating video {i+1}/{count} [{content_type}]")
        try:
            text = fetch_content(content_type)
            create_short(text, content_type, content_code)
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n✅ All videos saved in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
