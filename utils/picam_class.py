from picamera2 import Picamera2
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
import time

class Picam:
    def __init__(self, width=640, height=480):
        """
        Class to Initialize and manage the Raspberry Pi Camera using Picamera2.
        param width: Width of the camera frame (default is 640).
        param height: Height of the camera frame (default is 480).
        """
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (width, height)}))
        self.picam2.start()
        time.sleep(2)  # Allow camera to warm up
        print(f"Camera initialized with resolution {width}x{height}")

    def capture_image(self, filename=None, show_image=False, directory="../images"):
        """
        Function to capture an image and save it as 'image.jpg'.
        param filename: Name of the file to save the image as (default is the current timestamp).
        param show_image: Boolean flag to display the image after capturing (default is False).
        param directory: Directory to save the image (default is /images directory).
        """
        os.makedirs(directory, exist_ok=True)
        if filename is None:
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"img_{timestamp}.jpg"
        self.picam2.capture_file(os.path.join(directory, filename))
        print(f"Image captured and saved as '{filename} on {directory}'")
        if show_image:
            img_path = os.path.join(directory, filename)
            img = Image.open(img_path)
            plt.imshow(img)
            plt.axis('off')
            plt.show()

    def stop_camera(self):
        """
        Function to stop the camera.
        """
        self.picam2.stop()
        self.picam2.close()
        print(f"Camera stopped")