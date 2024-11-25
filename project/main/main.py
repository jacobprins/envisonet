from flask import Blueprint, render_template, url_for, redirect, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import glob
from pydub import AudioSegment

from .process import image_interpreter, speech_interpreter, speak, xaiprocess_semantic




# This creates a blueprint instance for "main.py".
main = Blueprint('main', __name__)

# These define the allowed audio and image extensions
ALLOWED_AUDIO_EXTENSIONS = {'webm'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# This is a function to check check if a given file has an allowed extension.
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions




# Default page route, redirects to service route.
@main.route('/')
def index():
    return redirect(url_for("main.service"))


# Service webpage route
@main.route('/service')
@login_required
def service():
    # Define the upload folder based on the user who is currently logged in
    username = current_user.id
    UPLOAD_FOLDER = f'FILES/files_for_{username}'

    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # When a request is posted, redirect to the /upload_files route
    if request.method == 'POST':
        return redirect(url_for('main.upload_files'))
    return render_template('/main/service.html')


# Uploading files to server route
@main.route('/upload_files', methods=['POST'])
@login_required
def upload_files():
    # Define the upload folder based on the user who is currently logged in
    username = current_user.id
    UPLOAD_FOLDER = f'FILES/files_for_{username}'

    # *terminal* indicate in the terminal that a post request was recieved and that the program has entered the "upload_files" route.
    print("Received a POST request for /upload_files") 

    # If an audio file and an image file posted, this handles the modaility.
    if 'audio' in request.files and 'image' in request.files:

        # Pulls audio and image files from the post request
        audio_file = request.files['audio']
        image_file = request.files['image']

        # Checks to see if the audio file is viable and has an allowed filetype
        if audio_file and allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
            # Malicious characters/strings protection for the audio file
            audio_filename = secure_filename(audio_file.filename)
            # Temporarily saves WebM audio file in the user's directory using the new file name
            audio_filepath = os.path.join(UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_filepath)

            # Converts the ".webm" audio file to a ".wav" audio file using pydub and requires ffmpeg to be installed to work properly
            try:
                webm_audio = AudioSegment.from_file(audio_filepath, format="webm")

                # Gets a filename that ends with ".wav" from the ".webm" filename
                wav_filename = audio_filename.rsplit('.', 1)[0] + '.wav'

                # Converts the ".webm" audio file to a ".wav" audio
                wav_filepath = os.path.join(UPLOAD_FOLDER, wav_filename)
                webm_audio.export(wav_filepath, format="wav")

                # Removes the temporary .webm audio file after conversion to ".wav"
                os.remove(audio_filepath)

                # Checks to see if the image file is viable and of a proper type
                if image_file and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):

                    # Malicious characters/strings protection for the image
                    image_filename = secure_filename(image_file.filename)

                    # Saves the image file file in the user's directory using the new file name
                    image_filepath = os.path.join(UPLOAD_FOLDER, image_filename)
                    image_file.save(image_filepath)

                    # Redirect to "/process_audio" with these files now saved
                    return redirect(url_for('main.process_image_audio_query', 
                                            audio_filepath=wav_filepath,
                                            image_filepath=image_filepath))
                # *error* returns a console messege and a 400 error if the image file is not viable.
                else:
                    return jsonify({'error': 'Invalid image file format'}), 400
            # *error* returns a console message and a 500 error if the audio conversion fails.    
            except Exception as e:
                return jsonify({'error': 'Error converting WebM to WAV', 'details': str(e)}), 500
        # *error* returns a console message and a 400 error if the audio file is not viable.
        else:
            return jsonify({'error': 'Invalid file format for audio or image'}), 400


    # If only an audio file is posted, this handles the modality. This system is the same as above, with image files removed
    elif 'audio' in request.files and 'image' not in request.files: #audio only submitted

        audio_file = request.files['audio']

        if audio_file and allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
            audio_filename = secure_filename(audio_file.filename)
            audio_filepath = os.path.join(UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_filepath)

            try:
                webm_audio = AudioSegment.from_file(audio_filepath, format="webm")
                wav_filename = audio_filename.rsplit('.', 1)[0] + '.wav'
                wav_filepath = os.path.join(UPLOAD_FOLDER, wav_filename)
                webm_audio.export(wav_filepath, format="wav")

                os.remove(audio_filepath)

                return redirect(url_for('main.process_audio_query', audio_filepath=wav_filepath,))
            
            except Exception as e:
                return jsonify({'error': 'Error converting WebM to WAV', 'details': str(e)}), 500
        else:
            return jsonify({'error': 'Invalid file format for audio or image'}), 400

        
    # If there are no files, this handles the modality
    elif 'audio' not in request.files or 'image' not in request.files:
        # This returns a 400 error no audio or image file are found
        return jsonify({'error': 'No audio or image file part'}), 400
    

# Route that processes the user query with an image and audio when called and ulitmately returns a spoken audio response
@main.route('/process_image_audio_query')
@login_required
def process_image_audio_query():
    # Defines the upload folder based on the user who is currently logged in
    username = current_user.id
    UPLOAD_FOLDER = f'FILES/files_for_{username}'

    # Gets the image and audio filepaths with arguments from the upload_files
    audio_filepath = request.args.get('audio_filepath')
    image_filepath = request.args.get('image_filepath')
    
    # Returns a 500 error if audio file or image file are not recieved
    if not audio_filepath or not image_filepath:
        os.remove(image_filepath)
        return jsonify({'error': 'Audio or image file path is missing'}), 500
    
    # Generates a transcript of the given audio file
    transcript = speech_interpreter(audio_filepath)
    
    # Returns url for the speechRecognition error audio file if no transcript could be obtained
    if not transcript:
        os.remove(image_filepath)
        return jsonify({
            'message': 'askAbout',
            'audio_url': "/static/audio/speechRecognitionError_response.mp3"
        }), 200
    
    # Generates a description of the given image using image_interpreter
    description = image_interpreter(image_filepath, transcript)

    # Removes the previous last image
    if(glob.glob(UPLOAD_FOLDER+"/lastimage.*")):
        os.remove(glob.glob(UPLOAD_FOLDER+"/lastimage.*")[0])

    # The image interpretation has been completed, so the image can now be renamed to last image for future use
    image_extention = image_filepath.rsplit('.', 1)[1]
    os.rename(image_filepath, f"{UPLOAD_FOLDER}/lastimage.{image_extention}")

    # Return a 500 error if image interpretation does not return
    if not description:
        return jsonify({'error': 'Could not interpret the image'}), 500

    # Generates TTS from "description" and saves it to the user's folder.
    speak(description, UPLOAD_FOLDER)

    # Returns a console message and the URL for the response audio file to be played in the frontend
    return jsonify({
        'message': 'Processing completed successfully',
        'audio_url': url_for('main.download_response_audio')
    }), 200


# Route that processes audio only queries
@main.route('/process_audio_query')
@login_required
def process_audio_query():
    # Defines the upload folder based on the user who is currently logged in
    username = current_user.id
    UPLOAD_FOLDER = f'FILES/files_for_{username}'

    # Gets the audio filepath with arguments from the upload_files
    audio_filepath = request.args.get('audio_filepath')
    
    # Gets lastImage filepath if it exists, assigns None otherwise
    if(glob.glob(UPLOAD_FOLDER+"/lastimage.*")):
        lastImage_filepath = glob.glob(UPLOAD_FOLDER+"/lastimage.*")[0]
    else:
        lastImage_filepath = None

    # Returns a 500 error if audio file or image file are not recieved
    if not audio_filepath:
        return jsonify({'error': 'Audio path is missing'}), 500
    
    # Generates a transcript of the given audio file
    transcript = speech_interpreter(audio_filepath)

    # Returns url for the speechRecognition error audio file if no transcript could be obtained
    if not transcript:
        return jsonify({
            'message': 'Speech Recognition Error',
            'audio_url': "/static/audio/speechRecognitionError_response.mp3"
        }), 200
    
    
    # With getting the semantic of the transcript, we are able to use xAI to respond with keywords which can trigger certian responses
    semantic = xaiprocess_semantic(transcript)

    if(semantic == "logout"):
        return(redirect(url_for("auth.logout")))
    
    elif(semantic == "askAbout"):
        return jsonify({
            'message': 'askAbout',
            'audio_url': "/static/audio/askabout_response.mp3"
        }), 200
    
    elif(semantic == "lastImage"):
        if(lastImage_filepath != None):
            description = image_interpreter(lastImage_filepath, transcript)
            speak(description, UPLOAD_FOLDER)
            return jsonify({
                'message': 'Processing completed successfully',
                'audio_url': url_for('main.download_response_audio')
            }), 200
        else:
            return jsonify({
                'message': 'Image History Error',
                'audio_url': "/static/audio/imageHistoryError_response.mp3"
            }), 200
        
    elif(semantic == "repeat"):
        return jsonify({
                'message': 'Processing completed successfully',
                'audio_url': url_for('main.download_response_audio')
            }), 200
    
    else:
        speak(semantic, UPLOAD_FOLDER)
        return jsonify({
            'message': 'Processing completed successfully',
            'audio_url': url_for('main.download_response_audio')
        }), 200


# Route that gets and returns the responseTTS.mp3 file
@main.route('/download_response_audio')
@login_required
def download_response_audio():
    # Define the upload folder based on the user who is currently logged in
    username = current_user.id
    UPLOAD_FOLDER = f'FILES/files_for_{username}'

    # Gets the filepath for "responseTTS.mp3"
    file_path = os.path.join(UPLOAD_FOLDER, "responseTTS.mp3")

    # If file exists, it is returned
    if os.path.exists(file_path):
        return send_from_directory(f"../{UPLOAD_FOLDER}", "responseTTS.mp3", as_attachment=True)
    
    # If file does not exist, 404 error is returned
    else:
        return jsonify({'error': 'File not found'}), 404


# If a page that does not exist is requested, the user is sent back to "/"
@main.app_errorhandler(404)
def page_not_found(e):
    return redirect(url_for("main.index"))
