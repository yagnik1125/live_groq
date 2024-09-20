import os
import time
import threading
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import wave
import io

# Initialize the Groq client
client = Groq(api_key="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")

# Streamlit frontend for audio input and translation
st.title("Audio Translation App")

# Audio file input
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg", "flac", "m4a"])
if uploaded_file:
    st.audio(uploaded_file, format="wav")

# Mic recorder setup
mic_audio = mic_recorder(start_prompt="🎙️ Start Recording", stop_prompt="🎙️ Stop Recording", key='recorder')

# Language selection for translation
selected_lang_tar = st.selectbox("Select the target language for translation", ['afrikaans', 'albanian', 'amharic', 'arabic', 'armenian', 'azerbaijani', 'basque', 'belarusian', 'bengali', 'bosnian', 'bulgarian', 'catalan', 'cebuano', 'chichewa', 'chinese (simplified)', 'chinese (traditional)', 'corsican', 'croatian', 'czech', 'danish', 'dutch', 'english', 'esperanto', 'estonian', 'filipino', 'finnish', 'french', 'frisian', 'galician', 'georgian', 'german', 'greek', 'gujarati', 'haitian creole', 'hausa', 'hawaiian', 'hebrew', 'hindi', 'hmong', 'hungarian', 'icelandic', 'igbo', 'indonesian', 'irish', 'italian', 'japanese', 'javanese', 'kannada', 'kazakh', 'khmer', 'korean', 'kurdish (kurmanji)', 'kyrgyz', 'lao','latin','latvian','lithuanian','luxembourgish','macedonian','malagasy','malay','malayalam','maltese','maori','marathi','mongolian','myanmar (burmese)','nepali','norwegian','odia','pashto','persian','polish','portuguese','punjabi','romanian','russian','samoan','scots gaelic','serbian','sesotho','shona','sindhi','sinhala','slovak','slovenian','somali','spanish','sundanese','swahili','swedish','tajik','tamil','telugu','thai','turkish','ukrainian','urdu','uyghur','uzbek','vietnamese','welsh','xhosa','yiddish','yoruba','zulu'])

# Flag to control live transcription
transcribing = False

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

def live_transcribe_and_translate():
    global transcribing
    full_transcription = ""
    full_translation = ""

    while transcribing:
        time.sleep(5)  # Wait for 5 seconds before capturing the next chunk

        if mic_audio:
            audio_bytes = mic_audio['bytes']
            if audio_bytes:
                # Save the audio chunk to a temporary file
                chunk_filename = "live_chunk.wav"
                with wave.open(chunk_filename, "wb") as wav_file:
                    sample_width = 2  # Sample width in bytes (16 bits)
                    channels = 1  # Mono
                    framerate = 44100  # Sample rate
                    
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(framerate)
                    wav_file.writeframes(audio_bytes)

                # Transcribe the chunk using Groq API
                with open(chunk_filename, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(chunk_filename, file.read()),
                        model="whisper-large-v3",
                        prompt="Transcribe",
                        response_format="json",
                        temperature=0.0,
                    )

                chunk_transcription_text = transcription.text
                full_transcription += chunk_transcription_text + " "

                # Translate the transcription
                chunk_translation = translate_text(chunk_transcription_text, selected_lang_tar)
                full_translation += chunk_translation + " "

                # Update the Streamlit interface with results in the main thread
                st.session_state.full_transcription = full_transcription
                st.session_state.full_translation = full_translation

# Start/Stop buttons for live transcription
if st.button("Start Live Transcription"):
    transcribing = True
    threading.Thread(target=live_transcribe_and_translate, daemon=True).start()

if st.button("Stop Live Transcription"):
    transcribing = False

# Display results if available
if "full_transcription" in st.session_state:
    st.write("Live Transcription:")
    st.write(st.session_state.full_transcription)

if "full_translation" in st.session_state:
    st.write("Live Translation:")
    st.write(st.session_state.full_translation)

# Debugging output to check if mic is capturing audio 
if mic_audio:
    st.write("Microphone is active. Listening...")
else:
    st.write("Microphone is not active.")

