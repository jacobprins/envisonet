import os
from gtts import gTTS
from speech_recognition import Recognizer, AudioFile
from openai import OpenAI
import base64
import requests
from pydub import AudioSegment

# Toggle to change between gTTS(True) and OpenAI(False) (no $ vs $)
freespeak = True

# Saved as environment variables for safety
OpenAI.api_key = os.environ.get("OPENAI_API_KEY")
xAI_API_KEY = os.environ.get("xAI_API_KEY")



# Function that, given an path to an audio file, will return a transcript of the speech in that audio file
def speech_interpreter(audio_path):
    # *terminal* indicate when the "speech_interpreter" function is running
    print("RUNNING SPEECH INTERPRETER")

    # Assign the recognizer function to the the variable, "r"
    r = Recognizer()
    try:
        # Given the path to an audiofile, get a transcript using google cloud speech recognition
        with AudioFile(audio_path) as source:
            audio = r.record(source)
        transcript = r.recognize_google(audio)
        
        # Print the transcript in the terminal
        print(transcript, "\n")
        
        # Return the transcript of the audio file
        return transcript
    
    # If speech interpretation fails, return the error and None
    except Exception as e:
        print(f"Error in speech interpretation\n")
    return None


# A function that, given an image path, will return a base64 encoding of that image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# A function that, given an image path and text, will return a description of an image based on two input modalities
def image_interpreter(image_path, transcript):
    # *terminal* indicate when the "image_interpreter" function is running
    print("RUNNING IMAGE INTERPRETER")

    # Assign the OpenAI function to the variable, "client"
    client = OpenAI()
        
    # Get the base64 encoding of the image
    base64_image = encode_image(image_path)

    # Using gpt-4o-mini, get a response for the two input modalities
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant for a blind person. Be concise and tell them about the important facts in the image. Your response should be a maximum of two sentences."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcript,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    description = response.choices[0].message.content

    # *terminal* print the response from gpt-4o-mini
    print(description, "\n")

    # Return the description
    return description

# A function that, given text and a directory path, will do TTS and save the file to the given directory
def speak(text, UPLOAD_FOLDER):
    # Indicate the the "speak" function is running
    print("RUNNING TEXT TO SPEECH")

    # Define the output path for the TTS audio file
    tts_audio_path = os.path.join(UPLOAD_FOLDER, "responseTTS.mp3")

    # Use Google TTS when the "freespeak" variable is true
    if freespeak == True:

        # Get text to speech from the given text using google TTS
        ttsFile = gTTS(text = text, lang='en', slow=False)

        # Saves the TTS file to "UPLOAD_FOLDER" as "responseTTS.mp3"
        ttsFile.save(tts_audio_path)

        boostedTtsFile = AudioSegment.from_mp3(tts_audio_path)
        boostedTtsFile = boostedTtsFile + 5
        boostedTtsFile.export(tts_audio_path, format='mp3')

        print(f"TTS audio saved successfully at {tts_audio_path}\n")

        # Return the audio file path
        return tts_audio_path
    
    # Use OpenAI TTS when the freespeak is false
    elif freespeak == False:
        # Initialize the OpenAI client
        client = OpenAI()

        # Make the TTS request
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        # Check if the response is valid
        if response is None:
            print("Error: No response received from TTS API.\n")
            return None

        # Read the binary audio content
        audio_content = response.read()
        if not audio_content:
            print("Error: No audio content in the response.\n")
            return None

        # Write the audio content to the file
        with open(tts_audio_path, "wb") as f:
            f.write(audio_content)

        boostedTtsFile = AudioSegment.from_mp3(tts_audio_path)
        boostedTtsFile = boostedTtsFile + 5
        boostedTtsFile.export(tts_audio_path, format='mp3')

        print(f"TTS audio saved successfully at {tts_audio_path}\n")
        return tts_audio_path

    else:
        print(f"Error in speak function:")
        return None
    
#using xAi for the "Semantic Engine" - returns keywords by interpreting the users speech 
def xaiprocess_semantic(transcript): 
    print("RUNNING SEMANTICS INTERPRETER")

    client = OpenAI(
        api_key = xAI_API_KEY,
        base_url="https://api.x.ai/v1"
    )

    completion = client.chat.completions.create(
    model="grok-beta",
    messages=[
        {"role": "system", "content": """
         
         With the text you have been given, your job is to decipher and fit it to a specific keyword. You will ONLY respond with the most appropriate keyword. 
         These keywords are given in the format (Interpreted request:keyword response). If the text best fits the decription of:

         The user wishes to log out, or anything relating to logging in/out:logout
         The user is asking about the last image. The text may have something similar to "In the last image":lastImage
         The user is specifically asking about what the website capabilities are, and is using a phrase such as "what can you do?":askAbout
         The user wants you to repeat yourself or what was said:repeat

         EXCEPTION TO KEYWORDS:
         If the user has a a request that does not relate to any other keyword requests, instead returning a keyword, respond to the question with a maximum of two sentences.
         
         """},
        {"role": "user", "content": transcript},
        ],
    )

    # Return the keyword
    response  = completion.choices[0].message.content
    print(response, "\n")
    return response