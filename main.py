import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from googletrans import Translator
from sudachipy import dictionary, tokenizer
from gtts import gTTS
import uuid
import jaconv  # ✅ Library untuk konversi Kana → Romaji

# ✅ Optional: set path dictionary Sudachi kalau perlu (Cloud Run / lokal Linux)
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

# ✨ Fungsi ubah ke bentuk keigo (-masu form)
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
        if word.endswith("aru"):
            words[i] = word[:-3] + masu_endings["aru"]
        elif word.endswith("iru"):
            words[i] = word[:-3] + masu_endings["iru"]
        elif word.endswith("iku"):
            words[i] = word[:-3] + masu_endings["iku"]
        elif word.endswith("ru"):
            words[i] = word[:-2] + masu_endings["ru"]

    return " ".join(words)

# 🔧 Pastikan input-nya selalu string
def convert_to_string(text) -> str:
    return str(text) if not isinstance(text, str) else text

# 📦 Endpoint utama
@app.post("/translate_and_analyze")
async def translate_and_analyze(request: TranslateRequest):
    text = convert_to_string(request.text)
    src = request.src
    dest = request.dest

    # Translate input (bisa romaji → kanji/kana otomatis)
    result = translator.translate(text, src=src, dest="ja")
    japanese_text = result.text

    # Konversi romaji → kanji otomatis oleh Google Translate
    romaji = ""
    if src == "ja":
        translated_result = translator.translate(japanese_text, src="ja", dest="id")
        final_translation = translated_result.text
    else:
        final_translation = japanese_text

    # Generate romaji dari Japanese text
    romaji_list = []
    for m in tokenizer_obj.tokenize(japanese_text, tokenizer.Tokenizer.SplitMode.C):
        reading = m.reading_form()
        romaji_word = jaconv.kana2alphabet(reading)
        romaji_list.append(romaji_word)
    romaji = " ".join(romaji_list)

    return JSONResponse(
        content={
            "translated_text": final_translation,
            "japanese_text": japanese_text,
            "romaji": romaji
        },
        media_type="application/json; charset=utf-8"
    )

# 🔊 Endpoint Text-to-Speech
@app.post("/speak")
async def speak_text(request: TranslateRequest):
    text = convert_to_string(request.text)

    filename = f"{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang=request.dest)
    tts.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speak.mp3")
