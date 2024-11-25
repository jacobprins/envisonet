const workerOptions = {
    OggOpusEncoderWasmPath: 'https://cdn.jsdelivr.net/npm/opus-media-recorder@latest/OggOpusEncoder.wasm',
    WebMOpusEncoderWasmPath: 'https://cdn.jsdelivr.net/npm/opus-media-recorder@latest/WebMOpusEncoder.wasm'
};

// Change media recorder API to the Opus Media Recorder API for more compatability 
window.MediaRecorder = OpusMediaRecorder;   

// Waits until the DOM content has been loaded before executing
document.addEventListener('DOMContentLoaded', () => {
    // Defines html elements
    const chooseImageButton = document.getElementById('chooseImageButton');
    const fileInput = document.getElementById('fileInput');
    const audioButton = document.getElementById('audioButton');

    // Defines media handling variables
    let audioRecorder;
    let audioChunks = [];
    let uploadedImage = null;

    // Function to start recording audio
    async function startRecording() {
        // Checks for invalid mic permissions
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Audio recording is not supported in this browser.");
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            let options = { mimeType: 'audio/webm' };
            audioRecorder = new MediaRecorder(stream, options, workerOptions);
            
            // Stores audio chunks
            audioRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            // Starts recording
            audioRecorder.start();
            console.log("Recording started.");

            // Waits for half a second before re-enabling the audio button
            setTimeout(() => {
                audioButton.disabled = false;
                audioButton.innerHTML = 'Stop Recording';
            }, 500);

        } catch (error) {
            console.error("Error accessing audio recording:", error);
        }
    } 

    // Function to send image and audio to the server
    async function sendFilesToServer(imageFile, audioBlob) {
        // Defines formData
        const formData = new FormData();
        
        // Appends both the image and audio files to FormData
        formData.append('image', imageFile);
        formData.append('audio', audioBlob, 'recorded_audio.webm');

        // Posts formData to the upload_files route in main.py
        try {
            const response = await fetch('/upload_files', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                // Dissapears the spinner and reload disclaimer
                document.getElementById('spinnerdiv').style.display = 'none';
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('reloadDisclaimer').style.display = 'none';
                
                const result = await response.json();
                console.log("Server response:", result);
                
                if (result.audio_url) {
                    // Sets the source of the audio player with a unique URL each time to ensure the source is refreshed
                    ttsAudioPlayer.src = result.audio_url + '?t=' + new Date().getTime();
                    // Sets the audioplayer volume to max
                    ttsAudioPlayer.volume = 1.0;
                    // Makes the audioplayer appear
                    ttsAudioPlayer.style.display = 'block';

                    // Requests fullscreen (can provide better audio playback)
                    const body = document.body;
                    if (body.requestFullscreen) {
                        body.requestFullscreen();
                    }

                    // Reloads the page when the audio clip has been completely played
                    ttsAudioPlayer.addEventListener('ended', () => {
                        console.log("Audio playback completed. Reloading page")
                        location.reload(); // Reload the page
                    });

                    // Auto-play the new audio
                    ttsAudioPlayer.play().catch(error => {
                        console.error("Error playing audio:", error);
                    });
                }
                
                else {
                    console.error("Server error:", response.statusText);
                    location.reload()
                }


            } 
            
            else {
                console.error("Server error:", response.statusText);
                location.reload()
            }
        } catch (error) {
            console.error("Error sending files to server:", error);
            location.reload()
        }
    }

    // Defines the audioplayer element
    const ttsAudioPlayer = document.getElementById('ttsAudioPlayer');


    // Handles file input change (for choose image)
    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            // Stores the uploaded image
            uploadedImage = file;
        }
    });

    let isFirstClick = true;

    // Waits for the audio button to be clicked
    audioButton.addEventListener('click', () => {
        // On first click, disables audio button, changes it to say starting, and starts recording
        if (isFirstClick) {
            audioButton.disabled = true;
            audioButton.innerHTML = 'Starting...';
            startRecording();
        
        // On second click, updates the page to a loading state
        } else {
            // Makes the interactive buttons disappear
            chooseImageButton.style.setProperty('display', 'none', 'important');
            audioButton.style.setProperty('display', 'none', 'important');
            
            // Spinner and reload disclaimer appear
            document.getElementById('waiting').style.display = 'block';
            document.getElementById('spinnerdiv').style.display = 'block';
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('reloadDisclaimer').style.display = 'block';
            
            // Disables the audio button
            audioButton.innerHTML = 'Request Sent';
            audioButton.disabled = true;

            // Stops recording and sends files
            if (audioRecorder && audioRecorder.state !== "inactive") {
                audioRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

                    if (uploadedImage && audioBlob) {
                        await sendFilesToServer(uploadedImage, audioBlob);
                        uploadedImage = null;
                        audioChunks = [];  // Clear chunks after sending
                    }
                    else if (audioBlob) {
                        await sendFilesToServer(uploadedImage, audioBlob);
                        uploadedImage = null;
                        audioChunks = [];  // Clear chunks after sending
                    }
                };
                audioRecorder.stop();
                console.log("Recording stopped.");
            }
            else {
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        }

        // Toggles the state
        isFirstClick = !isFirstClick;
    });
});