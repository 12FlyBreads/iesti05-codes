from flask import Flask, Response, render_template_string, request, redirect, url_for
from picamera2 import Picamera2
import io
import threading
import time
import os
import signal

app = Flask(__name__)

# Global Variables
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(os.path.dirname(script_dir), "../images")
width, height = 640, 480
picam2 = None
frame = None
frame_lock = threading.Lock()
shutdown_event = threading.Event()
capture_counts = {}

# Camera Functions
def initialize_camera():
    global picam2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (width, height)})
    picam2.configure(config)
    picam2.start()
    time.sleep(2)

def get_frame():
    global frame
    while not shutdown_event.is_set():
        stream = io.BytesIO()
        picam2.capture_file(stream, format='jpeg')
        with frame_lock:
            frame = stream.getvalue()
        time.sleep(0.1)

def generate_frames():
    while not shutdown_event.is_set():
        with frame_lock:
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

def shutdown_server():
    shutdown_event.set()
    if picam2:
        picam2.stop()
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGINT)

# Flask Routes
@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dataset Capture</title>
        </head>
        <body>
            <h1>Camera Stream & Capture</h1>
            <img src="{{ url_for('video_feed') }}" width="640" height="480" />
            
            <hr>

            <form action="/capture_image" method="post">
                <h3>Capture New Image</h3>
                <label for="subdirectory">Subfolder Name (optional):</label><br>
                <input type="text" name="subdirectory" placeholder="e.g., cats, dogs, ..."><br><br>
                
                <label for="filename">Custom Filename (optional, .jpg will be added):</label><br>
                <input type="text" name="filename" placeholder="e.g., cat_01, my_photo, ..."><br><br>
                
                <input type="submit" value="Capture Image">
            </form>

            <hr>
            <form action="/stop" method="post">
                <input type="submit" value="Stop Server" style="background-color: #ff6666;">
            </form>
        </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    if not shutdown_event.is_set():
        custom_subdirectory = request.form.get('subdirectory')
        custom_filename = request.form.get('filename')
        
        if custom_subdirectory:
            target_directory = os.path.join(base_dir, custom_subdirectory)
        else:
            target_directory = base_dir


        if custom_filename:
            if not custom_filename.lower().endswith('.jpg'):
                final_filename = custom_filename + ".jpg"
            else:
                final_filename = custom_filename
        else:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            final_filename = f"image_{timestamp}.jpg"

        os.makedirs(target_directory, exist_ok=True)
        
        full_path = os.path.join(target_directory, final_filename)
        picam2.capture_file(full_path)
        print(f"Image saved: {full_path}")

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    threading.Thread(target=shutdown_server).start()
    return "<h1>Server is shutting down...</h1><p>You can close this window.</p>"

# Main
if __name__ == '__main__':
    os.makedirs(base_dir, exist_ok=True)
    
    initialize_camera()
    threading.Thread(target=get_frame, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)