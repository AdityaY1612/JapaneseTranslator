import pyaudio
import wave
import keyboard
import requests
import json
import speech_recognition as sr
import time
# Set up PyAudio
audio = pyaudio.PyAudio()
stream = None

# Define constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

# Set up MyMemory API
base_url = "https://api.mymemory.translated.net/get"
lang_pair = "en|ja"

def start_recording():
    global stream
    print("Recording started")
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    while keyboard.is_pressed('z'):
        data = stream.read(CHUNK)
        frames.append(data)
    stop_recording(frames)

def stop_recording(frames):
    global stream
    print("Recording stopped")
    stream.stop_stream()
    stream.close()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe()

def transcribe():
    r = sr.Recognizer()
    with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
        audio_data = r.record(source)
    try:
        transcript = r.recognize_google(audio_data)
        print("Transcription: ", transcript)
        translate(transcript)
    except sr.UnknownValueError:
        print("Unable to transcribe audio")
    except sr.RequestError as e:
        print("Error occurred while accessing Google Speech Recognition service; {0}".format(e))

def translate(transcript):
    # Translate the transcription to Japanese using MyMemory API
    params = {"q": transcript, "langpair": lang_pair}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        translation = response.json()["responseData"]["translatedText"]
        print("Translation:", translation)
        VOICEVOX_API_URL = 'http://127.0.0.1:50021'
        TEXT = translation

        # Define headers and data for the API requests
        headers = {'Content-type': 'application/json'}
        audio_query_data = {'speaker': 16, 'text': TEXT}

        # Send a POST request to the audio_query route to get the synthesis query
        audio_query_response = requests.post(
            VOICEVOX_API_URL+"/audio_query?text="+TEXT+"&speaker=16", 
            headers=headers,
        )

        print(audio_query_response.json())


        # Wait for a while to give Voicevox time to generate the synthesis query
        time.sleep(5)

        # Send a POST request to the synthesis route with the synthesis query ID to get the audio data
        synthesis_response = requests.post(
            VOICEVOX_API_URL+"/synthesis?speaker=16",
            data=json.dumps(audio_query_response.json()),
            headers=headers
        )

        # Check if the request was successful and play the audio data using the system's default player
        if synthesis_response.status_code == 200:
            with open('output.wav', 'wb') as f:
                f.write(synthesis_response.content)
            import platform
            import subprocess
            if platform.system() == 'Darwin':
                subprocess.call(('open', 'output.wav'))
            elif platform.system() == 'Windows':
                subprocess.call(('start', 'output.wav'), shell=True)
            else:
                subprocess.call(('xdg-open', 'output.wav'))
        else:
            print('Error while synthesizing speech')
    else:
        print("Translation failed with status code", response.status_code)

print("Press and hold 'z' to start recording")
while True:
    if keyboard.is_pressed('z'):
        start_recording()
