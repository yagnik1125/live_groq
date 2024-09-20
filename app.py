import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import threading
from groq import Groq

# Initialize the Groq client
client = Groq(api_key="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")

# Streamlit frontend for audio input and translation
st.title("Live Audio Translation App")

# Language selection for translation
selected_lang_tar = st.selectbox("Select the target language for translation", ['afrikaans', 'albanian', 'amharic', 'arabic', 'armenian', 'azerbaijani', 'basque', 'belarusian', 'bengali', 'bosnian', 'bulgarian', 'catalan', 'cebuano', 'chichewa', 'chinese (simplified)', 'chinese (traditional)', 'corsican', 'croatian', 'czech', 'danish', 'dutch', 'english', 'esperanto', 'estonian', 'filipino', 'finnish', 'french', 'frisian', 'galician', 'georgian', 'german', 'greek', 'gujarati', 'haitian creole', 'hausa', 'hawaiian', 'hebrew', 'hindi', 'hmong', 'hungarian', 'icelandic', 'igbo', 'indonesian', 'irish', 'italian', 'japanese', 'javanese', 'kannada', 'kazakh', 'khmer', 'korean', 'kurdish (kurmanji)', 'kyrgyz','lao','latin','latvian','lithuanian','luxembourgish','macedonian','malagasy','malay','malayalam','maltese','maori','marathi','mongolian','myanmar (burmese)','nepali','norwegian','odia','pashto','persian','polish','portuguese','punjabi','romanian','russian','samoan','scots gaelic','serbian','sesotho','shona','sindhi','sinhala','slovak','slovenian','somali','spanish','sundanese','swahili','swedish','tajik','tamil','telugu','thai','turkish','ukrainian','urdu','uyghur','uzbek','vietnamese','welsh','xhosa','yiddish','yoruba','zulu'])

# Global variables
is_transcribing = False

def translate_text(text, targ_lang):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"Translate this text to '{targ_lang}'. Text:{text}. ONLY RETURN TRANSLATED TEXT DO NOT WRITE ANYTHING ELSE",
                }
            ],
            model="llama-3.1-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    # Convert the audio data to bytes
    audio_data = indata.copy()
    audio_bytes = audio_data.tobytes()

    # Process the audio bytes (transcription and translation)
    process_audio(audio_bytes)

def process_audio(audio_bytes):
    global is_transcribing
    
    # Save the audio chunk to a temporary file
    with wave.open("live_audio.wav", "wb") as wf:
        wf.setnchannels(1)  # Mono channel
        wf.setsampwidth(2)  # Sample width in bytes (16 bits)
        wf.setframerate(44100)  # Sample rate
        wf.writeframes(audio_bytes)

    # Transcribe the chunk using Groq API
    with open("live_audio.wav", "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(file.name, file.read()),
            model="whisper-large-v3",
            prompt="Transcribe",
            response_format="json",
            temperature=0.0,
        )

    chunk_transcription_text = transcription.text

    # Translate the transcription
    chunk_translation = translate_text(chunk_transcription_text, selected_lang_tar)

    # Display results in Streamlit app
    st.write(f"Chunk Transcription: {chunk_transcription_text}")
    st.write(f"Chunk Translation: {chunk_translation}")

def start_transcription():
    global is_transcribing
    is_transcribing = True
    
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100):
        while is_transcribing:
            sd.sleep(1000)  # Keep the stream alive

if st.button("Start Live Transcription"):
    threading.Thread(target=start_transcription, daemon=True).start()

if st.button("Stop Live Transcription"):
    is_transcribing = False

