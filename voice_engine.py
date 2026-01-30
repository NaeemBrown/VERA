import asyncio
import edge_tts
import pygame
import io

# VOICE: British Female (Polite)
VOICE = "en-GB-SoniaNeural"

async def _get_audio_stream(text):
    """Fetches audio bytes directly into memory (No hard drive usage)."""
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def speak(text):
    print(f"V.E.R.A.: {text}")
    try:
        # 1. Get bytes into RAM
        audio_bytes = asyncio.run(_get_audio_stream(text))
        
        # 2. Create a file-like object in memory
        audio_file = io.BytesIO(audio_bytes)
        
        # 3. Play from memory
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()

    except Exception as e:
        print(f"Voice Error: {e}")