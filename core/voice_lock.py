import os
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
import librosa
import io
import sounddevice as sd

# --- PATH SETUP ---
# Calculate root to find the data folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
MASTER_VOICE_FILE = os.path.join(DATA_DIR, "naeem_voice.npy")

# SECURITY CONFIG
SIMILARITY_THRESHOLD = 0.60  # Lenient setting


class VoiceSecurity:
    def __init__(self):
        print("DEBUG: Loading Neural Voice Engine...")
        self.encoder = VoiceEncoder()
        self.master_embed = self.load_master_voice()

    def load_master_voice(self):
        if os.path.exists(MASTER_VOICE_FILE):
            try:
                return np.load(MASTER_VOICE_FILE)
            except:
                return None
        return None

    def enroll_user(self):
        """Records the user to create a master voice print."""
        print("Please speak naturally for 6 seconds...")
        fs = 16000
        seconds = 6

        # Record
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()

        # Process
        print("Processing voice print...")
        processed_wav = preprocess_wav(recording.flatten())
        embed = self.encoder.embed_utterance(processed_wav)

        # Ensure data folder exists
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        # Save
        np.save(MASTER_VOICE_FILE, embed)
        self.master_embed = embed
        print(f"Voice Identity Saved to {MASTER_VOICE_FILE}")

    def verify_audio(self, audio_object):
        """Checks if the speech_recognition AudioData matches the user."""
        if self.master_embed is None:
            print("WARNING: No master voice found. Security is OPEN.")
            return True

        try:
            # Convert AudioData to raw bytes (16kHz mono)
            wav_bytes = audio_object.get_wav_data(convert_rate=16000, convert_width=2)
            wav_stream = io.BytesIO(wav_bytes)

            # Load with Librosa
            wav, source_sr = librosa.load(wav_stream, sr=16000)

            # Embed & Compare
            processed_wav = preprocess_wav(wav)
            embed = self.encoder.embed_utterance(processed_wav)
            score = np.dot(embed, self.master_embed)

            print(f"DEBUG: Voice Match Score: {score:.2f}")
            return score > SIMILARITY_THRESHOLD

        except Exception as e:
            print(f"Verification Error: {e}")
            return False


# Create a singleton instance
security_system = VoiceSecurity()
