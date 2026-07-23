"""
MIT License

Copyright (c) 2026 Clarke Yoursa Tee
"""

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn
import io

from sovereign_tts import SovereignTTS

app = FastAPI(title="SovereignTTS API", version="1.0")

tts = SovereignTTS()

@app.get("/speak")
async def speak(
    text: str = Query(..., description="Text for the Dragon to speak"),
    filename: str = "dragon_output.wav"
):
    audio_bytes = tts.synthesize(text)
    
    # Optional: save to file
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    
    return FileResponse(
        filename,
        media_type="audio/wav",
        filename=filename
    )

@app.get("/speak/stream")
async def speak_stream(text: str = Query(...)):
    audio_bytes = tts.synthesize(text)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")

@app.get("/health")
async def health():
    return tts.health()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)