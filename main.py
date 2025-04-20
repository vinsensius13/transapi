import os
import uuid
import jaconv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from googletrans import Translator
from sudachipy import dictionary, tokenizer
from gtts import gTTS

# ✅ Optional: buat Linux/Cloud Run
os.environ["SUDACHIDICT_DIR"] = "/usr/local/lib/python3.10/dist-packages/sudachidict_core"

app = FastAPI()
translator = Translator()
tokenizer_obj = dictionary.Dictionary().create()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TransAPI is alive! 🔥"}

# 🧠 Model request
class TranslateRequest(BaseModel):
    text: str
    src: str = "id"
    dest: str = "ja"

# ✨ Optional: ubah ke keigo (-masu form)
def to_keigo(text: str) -> str:
    masu_endings = {
        "aru": "あります",
        "iru": "います",
        "iku": "行きます",
        "ru": "ます",
    }
    words = text.split()
    for i in range(len(words)):
        word = words[i]
        for key in masu_endings:
            if word.endswith(key):
                words[i] = word[:-len(key)] + masu_endings[key]
                break
    return " ".join(words)

# 🔧 Force string
def convert_to_string(text) -> str:
    return str(text) if not isinstance(text, str) else text

@app.post("/translate_and_analyze")
async def translate_and_analyze(request: TranslateRequest):
    text = convert_to_string(request.text)
    src = request.src.lower()
    dest = request.dest.lower()

    # 🌸 Deteksi apakah input user adalah romaji (jika input-nya dianggap Jepang)
    if src == "ja":
        is_romaji = all(ord(c) < 128 and (c.isalnum() or c.isspace()) for c in text)
        if is_romaji:
            # romaji ke kana (hiragana/katakana auto oleh jaconv)
            kana_text = jaconv.alphabet2kana(text)
        else:
            kana_text = text

        japanese_text = kana_text

        # Translate ke Bahasa Indonesia
        translated = translator.translate(japanese_text, src="ja", dest="id")
        final_translation = translated.text
    else:
        # Dari Indonesia ke Jepang
        translated = translator.translate(text, src=src, dest="ja")
        japanese_text = translated.text

        # Translate hasil Jepang ke target dest (misal: id)
        if dest == "ja":
            final_translation = japanese_text
        else:
            result_back = translator.translate(japanese_text, src="ja", dest=dest)
            final_translation = result_back.text

    # 🔠 Generate romaji dari hasil Japanese text
    romaji_list = []
    for token in tokenizer_obj.tokenize(japanese_text, tokenizer.Tokenizer.SplitMode.C):
        reading = token.reading_form()
        hira = jaconv.kata2hira(reading)
        romaji = jaconv.kana2alphabet(hira)
        romaji_list.append(romaji)

    romaji_output = " ".join(romaji_list)

    return JSONResponse(
        content={
            "translated_text": final_translation,
            "japanese_text": japanese_text,
            "romaji": romaji_output
        },
        media_type="application/json; charset=utf-8"
    )

# 🔊 TTS
@app.post("/speak")
async def speak_text(request: TranslateRequest):
    text = convert_to_string(request.text)

    filename = f"{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang=request.dest)
    tts.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speak.mp3")
