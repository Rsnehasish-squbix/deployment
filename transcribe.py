import base64
import io
import requests
import wave
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = os.getenv('GROQ_API_URL')

if not GROQ_API_KEY or not GROQ_API_URL:
    raise EnvironmentError("GROQ_API_KEY or GROQ_API_URL is missing in the environment variables.")

def decode_base64_to_audio_file(b64_str):
    try:
        b64_str = b64_str.replace("\n", "").replace("\r", "").strip()

        audio_data = base64.b64decode(b64_str)
        audio_stream = io.BytesIO(audio_data)
        audio_stream.name = "input_audio"

        input_format = detect_audio_format(audio_stream)
        print(f"Detected audio format: {input_format}")

        audio_stream = reencode_audio(audio_stream, input_format)
        return audio_stream
    except Exception as e:
        raise ValueError(f"Failed to decode base64 string to audio: {e}")

def detect_audio_format(audio_stream):
    try:
        audio_stream.seek(0)
        temp_input = "temp_input"
        with open(temp_input, "wb") as f:
            f.write(audio_stream.read())

        result = subprocess.run(
            ["ffprobe", "-i", temp_input, "-show_entries", "format=format_name", "-v", "quiet", "-of", "csv=p=0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        os.remove(temp_input)

        if result.returncode != 0:
            raise ValueError("Unable to detect audio format.")

        return result.stdout.strip()
    except Exception as e:
        raise ValueError(f"Error detecting audio format: {e}")

def reencode_audio(audio_stream, input_format):
    try:
        audio_stream.seek(0)
        temp_input = f"input.{input_format}"
        temp_output = "output.wav"

        with open(temp_input, "wb") as f:
            f.write(audio_stream.read())

        subprocess.run(
            ["ffmpeg", "-y", "-i", temp_input, "-ar", "16000", "-ac", "1", temp_output],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        with open(temp_output, "rb") as f:
            reencoded_audio = io.BytesIO(f.read())
            reencoded_audio.name = "audio.wav"

        os.remove(temp_input)
        os.remove(temp_output)

        return reencoded_audio
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        raise RuntimeError(f"Failed to re-encode audio file: {e}")

def transcribe_audio(audio_stream):
    try:
        audio_stream.seek(0)
        files = {'file': ("audio.wav", audio_stream, 'audio/wav')}
        headers = {'Authorization': f'Bearer {GROQ_API_KEY}'}
        data = {'model': 'whisper-large-v3-turbo'}

        print(f"Sending request to {GROQ_API_URL}...")
        response = requests.post(GROQ_API_URL, headers=headers, files=files, data=data)

        # print(f"Response Status Code: {response.status_code}")
        # print(f"Response JSON: {response.json()}")

        if response.status_code == 200:
            transcription = response.json().get('text', 'No transcription found')
            print(f"Transcription: {transcription}")
            return transcription
        else:
            raise ValueError(f"GROQ API error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request to GROQ API failed: {e}")
    except Exception as e:
        raise ValueError(f"Error during transcription: {e}")

def process_b64_str(b64_str):
    try:
        audio_stream = decode_base64_to_audio_file(b64_str)
        transcription = transcribe_audio(audio_stream)
        return transcription
    except Exception as e:
        raise RuntimeError(f"Processing error: {e}")