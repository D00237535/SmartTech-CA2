import socketio
import eventlet
from flask import Flask
from keras.models import load_model
import base64 
from io import BytesIO
from PIL import Image
import numpy as np
import cv2 
import socket

speed_limit = 10

sio = socketio.Server()

app = Flask(__name__)

listen_socket = eventlet.listen(('', 4567))

def img_preprocess(img):
    print("preprocessing...")
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, [3, 3], 0)
    img = cv2.resize(img, (200, 66))
    img = img/255 #normalizing
    return img


def send_control(steering_angle, throttle):
     print("sending control")
     sio.emit('steer', data={'steering_angle': steering_angle.__str__(), 'throttle':throttle.__str__()})

@sio.on('telemetry')
def telemetry(session_id, data):
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    steering_angle = float(model.predict(image))
    speed = float(data['speed'])
    throttle = 1.0 - speed/speed_limit
    send_control(steering_angle, throttle)

@sio.on('connect')
def connect(sid, environ):
    print("Connected")
    send_control(0, 0) # don't want car to move when connecting


if __name__ == '__main__':
    try:
        model = load_model('alpha_model.h5')
        app = socketio.Middleware(sio, app)
        eventlet.wsgi.server(listen_socket, app)
    except Exception as ex:
        print(ex)