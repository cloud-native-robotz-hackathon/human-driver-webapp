#!/usr/bin/python3
from flask import Flask
from flask import render_template
from flask import request
from flask import Response
import logging
import threading
import time
import os
import cv2
import base64
import requests

import numpy as np
import random
from matplotlib import pyplot as plt

from lib.preprocessing import preprocess_encoded_image
from lib.object_detection import detect_objects

from pprint import pformat

# import torch
# from classes import classes
# from preprocessing import preprocess_image_file
# from object_detection import postprocess
# from object_rendering import draw_boxes

output_frame = None
lock = threading.Lock()

app = Flask(__name__)
# WEB_LOGLEVEL=['INFO','DEBUG']..
app.logger.setLevel(level=os.environ.get('WEB_LOGLEVEL', 'INFO').upper())

@app.route('/healthz')
def healthz():
    """
    Check the health of this peakweb instance. OCP will hit this endpoint to verify the readiness
    of the peakweb pod.
    """
    return 'OK'

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/camera")
def camera():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate_video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

def add_name_box(frame, left, top, bottom, right, name, color):
    # inv_ratio = 1.0 / 1.0
    # top = int(top * inv_ratio)
    # right = int(right * inv_ratio)
    # bottom = int(bottom * inv_ratio)
    # left = int(left * inv_ratio)
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


def generate_video_feed():

    # grab global references to the output frame and lock variables
    global output_frame,lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            img_response = requests.get('http://terminator.robot.lan:5000/camera', verify=False)
            output_frame = base64.b64decode(img_response.text)

            raw_image,(image_data, ratio, dwdh) = preprocess_encoded_image(img_response.text)
            class_labels = ['Laptop', 'Computer keyboard', 'Fedora']

            objects = detect_objects(
                image_data,
                'http://192.168.66.64:8000/v2/models/robot_onnx/infer',
                token='',
                classes_count=len(class_labels),
                confidence_threshold=0.15,
                iou_threshold=0.2
            )

            app.logger.info('Detected obejects:')
            app.logger.info(pformat(objects))
            app.logger.info(pformat(objects.tolist()))
            
            for (top, right, bottom, left, score, cls_id) in objects.tolist() :
                name = class_labels[int(cls_id)]
                app.logger.info(name)
                # Green
                color = (0, 153, 51)
                if name == "Unknown":
                    # Red
                    color = (0, 0, 255)
                app.logger.info("Add Box: %d %d %d %d",int(left), int(top), int(bottom), int(right))
                add_name_box(raw_image, int(left), int(top), int(bottom), int(right), name, color)
            
            encode_state, encoded_image = cv2.imencode('.jpg', raw_image )
            cv2.imwrite("camera.jpg", raw_image) 
            # yield the output frame in the byte format
            yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n'

        time.sleep(0.5)


