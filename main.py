import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from googletrans import Translator
from sudachipy import dictionary, tokenizer

# ✅ Set manual path dictionary Sudachi (optional, bisa dihapus kalau gak perlu di Cloud Run)
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

@app.get("/")  # ← INI DIA
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

    result = translator.translate(text, src=src, dest=dest)
    translated_text = result.text
    translated_text_keigo = to_keigo(translated_text)

    tokens = []
    if dest == "ja":
        for m in tokenizer_obj.tokenize(translated_text_keigo, tokenizer.Tokenizer.SplitMode.C):
            tokens.append({
                "surface": m.surface(),
                "pos": ",".join(m.part_of_speech()),
                "dictionary_form": m.dictionary_form(),
                "reading": m.reading_form()
            })

    return {
        "translated_text": translated_text_keigo,
        "tokens": tokens
    }
