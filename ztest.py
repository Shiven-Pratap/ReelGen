import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from elevenlabs import play # Optional: for playing audio directly

# !!! WARNING: Hardcoding API keys is NOT recommended for production environments !!!
# This is for demonstration purposes only.

API_KEY = "sk_6f557e62d7a62fe61aaabd270d8bb95804a5adddbf823eff" # Replace with your actual Eleven Labs API key


if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
    print("Error: Please replace 'YOUR_API_KEY_HERE' with your actual Eleven Labs API key.")
else:
    # Initialize the ElevenLabs client
    client = ElevenLabs(
        api_key=API_KEY,
    )

    # The text you want to convert to speech
    text_to_convert = "Hello, this is a test from Eleven Labs using Python! Playing directly."

    # Choose a voice ID (you can find available voice IDs in your Eleven Labs dashboard or via the API)
    # Example voice ID for 'Adam': pNInz6obpgDQGcFmaJgB
    voice_id = "pNInz6obpgDQGcFmaJgB" # You can change this to your preferred voice ID

    try:
        # Convert text to speech
        audio_response = client.text_to_speech.convert(
            text=text_to_convert,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128", # Output format is still needed for the stream
        )

        print("Playing audio directly...")
        # Play the audio directly
        # Requires an audio player like 'mpv' or 'ffmpeg' installed on your system.
        play(audio_response)
        print("Audio playback finished.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have an audio player like 'mpv' or 'ffmpeg' installed on your system for direct playback.")