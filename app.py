from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import pandas as pd
import base64
import threading
import logging
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli_anahtar123'
socketio = SocketIO(app, cors_allowed_origins="*")


if not os.path.exists("database"):
    os.makedirs("database")
if not os.path.exists("database/encodings"):
    os.makedirs("database/encodings")
if not os.path.exists("database/users.csv"):
    pd.DataFrame(columns=["id", "isim", "kayit_tarihi"]).to_csv("database/users.csv", index=False)


camera = None
camera_lock = threading.Lock()
is_streaming = False
current_frame = None
frame_lock = threading.Lock()

def load_users():
    """Kullanıcı veritabanını yükle"""
    if os.path.exists("database/users.csv"):
        return pd.read_csv("database/users.csv")
    return pd.DataFrame(columns=["id", "isim", "kayit_tarihi"])

def init_camera():
    """Kamerayı başlat"""
    global camera
    with camera_lock:
        if camera is None:
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera is not None

def release_camera():
    """Kamerayı kapat"""
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

def process_frame(frame, mode="detection"):
    """Frame'i işle"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    
    if mode == "detection":
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        users_df = load_users()
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Bilinmeyen"
            
            try:
                if not users_df.empty:
                    for _, row in users_df.iterrows():
                        encoding_path = f"database/encodings/{row['id']}.npy"
                        if os.path.exists(encoding_path):
                            user_encoding = np.load(encoding_path)
                            match = face_recognition.compare_faces([user_encoding], face_encoding, tolerance=0.6)[0]
                            if match:
                                name = row['isim']
                                break
            except Exception as e:
                logger.error(f"Yüz karşılaştırma hatası: {str(e)}")
            
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
    
    else:
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            if len(face_locations) == 1:
                cv2.putText(frame, "Yuz Tespit Edildi", (left, top - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame, len(face_locations) == 1

def frame_to_base64(frame):
    """Frame'i base64'e dönüştür"""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/register')
def register():
    """Kayıt sayfası"""
    return render_template('register.html')

@socketio.on('start_stream')
def start_stream(data):
    """Video akışını başlat"""
    global is_streaming
    mode = data.get('mode', 'detection')
    
    if init_camera():
        is_streaming = True
        threading.Thread(target=stream_video, args=(mode,)).start()
    else:
        emit('error', {'message': 'Kamera başlatılamadı'})

@socketio.on('stop_stream')
def stop_stream():
    """Video akışını durdur"""
    global is_streaming
    is_streaming = False
    release_camera()

def stream_video(mode):
    """Video akışı döngüsü"""
    global is_streaming, current_frame
    
    while is_streaming:
        with camera_lock:
            if camera is None or not camera.isOpened():
                break
            ret, frame = camera.read()
            if not ret:
                break
            
 
            processed_frame, face_detected = process_frame(frame, mode)
            
            with frame_lock:
                current_frame = processed_frame.copy()
            
 
            frame_data = frame_to_base64(processed_frame)
            socketio.emit('frame', {
                'frame': frame_data,
                'face_detected': face_detected
            })
    
    release_camera()

def check_face_exists(face_encoding):
    """Verilen yüz kodlamasının veritabanında olup olmadığını kontrol et"""
    users_df = load_users()
    if users_df.empty:
        return False, None
    
    try:
        for _, row in users_df.iterrows():
            encoding_path = f"database/encodings/{row['id']}.npy"
            if os.path.exists(encoding_path):
                saved_encoding = np.load(encoding_path)
                match = face_recognition.compare_faces([saved_encoding], face_encoding, tolerance=0.6)[0]
                if match:
                    return True, row['isim']
        return False, None
    except Exception as e:
        logger.error(f"Yüz karşılaştırma hatası: {str(e)}")
        return False, None

@socketio.on('take_photo')
def take_photo(data):
    """Fotoğraf çek ve kullanıcı kaydet"""
    name = data.get('name')
    
    with frame_lock:
        if current_frame is None:
            emit('error', {'message': 'Frame bulunamadı'})
            return
        
        frame = current_frame.copy()
    
    try:

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        

        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) != 1:
            emit('error', {'message': 'Fotoğrafta tam olarak bir yüz tespit edilemedi'})
            return
        
 
        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        
    
        exists, existing_name = check_face_exists(face_encoding)
        if exists:
            emit('error', {
                'message': f'Bu yüz zaten "{existing_name}" adıyla kayıtlı! Lütfen farklı bir kişi için kayıt yapın.'
            })
            return
        

        user_id = datetime.now().strftime("%Y%m%d%H%M%S")
        

        np.save(f"database/encodings/{user_id}.npy", face_encoding)
        
 
        users_df = load_users()
        new_user = pd.DataFrame({
            "id": [user_id],
            "isim": [name],
            "kayit_tarihi": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        users_df.to_csv("database/users.csv", index=False)
        
        emit('success', {'message': 'Kullanıcı başarıyla kaydedildi'})
        
    except Exception as e:
        logger.error(f"Kullanıcı kayıt hatası: {str(e)}")
        emit('error', {'message': f'Kullanıcı kaydı sırasında hata oluştu: {str(e)}'})

@app.route('/users')
def get_users():
    """Kullanıcı listesini getir"""
    users_df = load_users()
    return jsonify(users_df.to_dict('records'))

if __name__ == '__main__':
    socketio.run(app, debug=True) 