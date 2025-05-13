import requests

def generate_audio_from_transcript(transcript, api_key, output_path="output.mp3", voice_id="21m00Tcm4TlvDq8ikWAM"):
    """
    Tạo file audio từ transcript bằng ElevenLabs API.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": transcript,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(output_path, "wb") as audio_file:
            audio_file.write(response.content)
        print(f"Audio đã được lưu tại: {output_path}")
    else:
        raise Exception(f"Lỗi API ElevenLabs: {response.status_code} - {response.text}")