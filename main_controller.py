# main_controller.py
# 美化网页
# 使用方法：终端开启虚拟环境source /home/sws21/Desktop/my_yolo/bin/activate
# 修好了延迟一个画面的问题
import os
import time
import threading
import io
import serial
import sys
import termios
import tty
import atexit
import select
import json
import numpy as np
from PIL import Image
import paho.mqtt.client as mqtt
import collections

from flask import Flask, Response, render_template_string, request, jsonify
from picamera2 import Picamera2
import cv2 # For image processing and YOLO
from ultralytics import YOLO # Added for YOLO detection

# ==================== Configuration (配置) ====================
# --- Camera Settings ---
FRAME_WIDTH = 640  # Lower resolution for faster processing
FRAME_HEIGHT = 320 # Lower resolution for faster processing
TARGET_FPS = 30    # Target a higher FPS for smoother video

# --- Serial Port Settings ---
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200

# --- Photo Settings ---
PHOTO_DIRECTORY = "photos"

# --- MQTT Settings ---
MQTT_BROKER_HOSTNAME = "192.168.137.229"
MQTT_USERNAME = "Wang"
MQTT_PASSWORD = "Chenghao"
MQTT_MESSAGE_TOPIC = "Group21/message"

# --- YOLO Settings ---
YOLO_MODEL_PATH = '/home/sws21/Desktop/web/best.pt' # Path to your YOLO model yolov8n
DETECTION_FRAME_SKIP = 10 # Reduced for more responsive control
CENTER_TOLERANCE = 50 # Pixels from center o be considered "aligned"

# ==================== Global Variables (全局变量) ====================
app = Flask(__name__)
picam2 = Picamera2()
frame_buffer = None
frame_ready = threading.Condition()


# --- YOLO and Detection Thread Globals ---
yolo_model = None # Will be loaded in main
yolo_detection_active = False
yolo_detection_lock = threading.Lock()

# Queue for passing frames to the detection thread
# maxlen=1 ensures the detection thread always gets the latest frame, dropping old ones.
detection_frame_queue = collections.deque(maxlen=1) 
latest_boxes = [] # Stores the latest detected bounding boxes
latest_boxes_lock = threading.Lock()


# Initialize serial port
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"Error: Could not open serial port {SERIAL_PORT}. Please check if the port is correct and you have permissions.")
    print(e)
    ser = None

# MQTT Client global instance
mqtt_client = None

# Message queue for SSE (Server-Sent Events)
sse_message_queue = collections.deque()
sse_message_ready = threading.Condition()

cargo = 'null'
my_cargo2 = 'null' #in practical, start with 'null' both
cargo_times = 0 #记录现在的状态


# ==================== MQTT Functions (from send.py) ====================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected")
        client.subscribe(MQTT_MESSAGE_TOPIC)
        with sse_message_ready:
            sse_message_queue.append({"type": "status", "message": "MQTT 连接成功!"})
            sse_message_ready.notify_all()
    else:
        print(f"MQTT Failed to connect. Error code: {rc}")
        with sse_message_ready:
            sse_message_queue.append({"type": "status", "message": f"MQTT 连接失败! 错误码: {rc}"})
            sse_message_ready.notify_all()

def on_message(client, userdata, msg):
    global cargo, my_cargo2
    topic = msg.topic
    try:
        message_content = msg.payload.decode('utf-8')
        print(f"Received message: {message_content}")
        # print("tag")
        # print(type(message_content))
        
        str_list = message_content.split(' ')
        cargo = str_list[0]
        my_cargo2 = str_list[1]
        # print(type(cargo))
        print('---------------------' + cargo)
        print('---------------------' + my_cargo2)
        with sse_message_ready:
            sse_message_queue.append({"type": "mqtt_result", "message": f"收到消息: {message_content}"})
            sse_message_ready.notify_all()
    except Exception as e:
        print(f"Error processing MQTT message: {e}")
        with sse_message_ready:
            sse_message_queue.append({"type": "error", "message": f"处理MQTT消息错误: {e}"})
            sse_message_ready.notify_all()

def setup_mqtt_client(hostname):
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(hostname)
        client.loop_start()
        print(f"Attempting to connect to MQTT broker at {hostname}...")
        return client
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return None





# ==================== HTML & JavaScript Template ====================
# Make sure to use a standard triple-quoted string, NOT an f-string (f"""...""").
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyberpunk Smart Car Control Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400..900&family=Turret+Road:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #01040a;
            --primary-glow-color: #00e5ff;
            --secondary-glow-color: #ff00ff;
            --danger-glow-color: #ff1b4c;
            --success-glow-color: #2eff7b;
            --text-color: #e6f1ff;
            --panel-bg: rgba(10, 25, 47, 0.85);
            --panel-border: rgba(0, 229, 255, 0.3);
            --panel-shadow: 0 0 15px rgba(0, 229, 255, 0.2), 0 0 25px rgba(0, 229, 255, 0.1);
            --font-primary: 'Orbitron', sans-serif;
            --font-secondary: 'Turret Road', sans-serif;
        }

        @keyframes flicker {
            0%, 18%, 22%, 25%, 53%, 57%, 100% {
                text-shadow:
                    0 0 4px #fff,
                    0 0 11px var(--primary-glow-color),
                    0 0 19px var(--primary-glow-color),
                    0 0 40px var(--primary-glow-color);
            }
            20%, 24%, 55% { text-shadow: none; }
        }

        body {
            font-family: var(--font-secondary), sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background-color: var(--bg-color);
            background-image: 
                linear-gradient(rgba(0, 229, 255, 0.07) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 229, 255, 0.07) 1px, transparent 1px);
            background-size: 35px 35px;
            color: var(--text-color);
            overflow-x: hidden;
        }

        .container {
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            width: 95%;
            max-width: 1200px;
            padding: 25px;
            box-sizing: border-box;
            background-color: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            box-shadow: var(--panel-shadow);
            backdrop-filter: blur(10px);
        }
        
        /* Decorative corner brackets */
        .container::before, .container::after,
        .container > .corner-top-right::before, .container > .corner-bottom-left::before {
            content: '';
            position: absolute;
            width: 25px;
            height: 25px;
            border-color: var(--primary-glow-color);
            border-style: solid;
            opacity: 0.7;
        }
        .container::before { top: 10px; left: 10px; border-width: 2px 0 0 2px; }
        .container::after { top: 10px; right: 10px; border-width: 2px 2px 0 0; }
        .container > .corner-top-right::before { bottom: 10px; right: 10px; border-width: 0 2px 2px 0; }
        .container > .corner-bottom-left::before { bottom: 10px; left: 10px; border-width: 0 0 2px 2px; }


        h1 {
            font-family: var(--font-primary);
            color: var(--text-color);
            font-weight: 700;
            margin: 0;
            animation: flicker 3s infinite linear;
            font-size: 2.2rem;
            order: 1; /* Order for flexbox layout */
        }
        
        .target-display {
            order: 2;
            width: 100%;
            text-align: center;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            background: rgba(0,0,0,0.2);
        }
        .target-display h2 {
            margin: 0 0 5px 0;
            font-family: var(--font-primary);
            font-size: 1rem;
            color: var(--secondary-glow-color);
            text-shadow: 0 0 8px var(--secondary-glow-color);
        }
        .target-display p {
            margin: 0;
            font-size: 1.2rem;
            color: var(--text-color);
            font-weight: 700;
        }

        .video-wrapper {
            order: 3;
            position: relative;
            width: 100%;
            max-width: 960px;
            aspect-ratio: 2 / 1;
            border-radius: 12px;
            overflow: hidden;
            background-color: #000;
            border: 2px solid var(--primary-glow-color);
            box-shadow: 0 0 25px var(--primary-glow-color), inset 0 0 15px rgba(0, 229, 255, 0.5);
        }
        
        .video-wrapper::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to bottom, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.05) 50%, rgba(0,0,0,0) 50.1%, rgba(0,0,0,0) 100%);
            background-size: 100% 4px;
            z-index: 3;
            pointer-events: none;
            opacity: 0.5;
        }

        .video-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1;
        }

        .video-stream {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }

        .controls-overlay {
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(3, 1fr);
            gap: 12px;
            width: 180px;
            height: 180px;
            z-index: 10;
        }

        .control-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-glow-color);
            background-color: rgba(0, 229, 255, 0.1);
            border: 2px solid var(--primary-glow-color);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
            text-shadow: 0 0 8px var(--primary-glow-color);
            box-shadow: inset 0 0 8px rgba(0, 229, 255, 0.5);
        }

        .control-btn:hover {
            background-color: rgba(0, 229, 255, 0.3);
            color: #fff;
            box-shadow: 0 0 15px var(--primary-glow-color), inset 0 0 10px rgba(0, 229, 255, 0.7);
        }

        .control-btn:active {
            transform: scale(0.95);
            box-shadow: 0 0 25px var(--primary-glow-color), inset 0 0 15px rgba(0, 229, 255, 1);
        }

        .forward { grid-column: 2; grid-row: 1; }
        .left { grid-column: 1; grid-row: 2; }
        .stop {
            grid-column: 2;
            grid-row: 2;
            background-color: rgba(255, 27, 76, 0.1);
            border-color: var(--danger-glow-color);
            color: var(--danger-glow-color);
            border-radius: 50%;
            font-size: 1.6rem;
            text-shadow: 0 0 8px var(--danger-glow-color);
            box-shadow: inset 0 0 8px rgba(255, 27, 76, 0.5);
        }
        .stop:hover {
            background-color: rgba(255, 27, 76, 0.3);
            color: #fff;
            box-shadow: 0 0 15px var(--danger-glow-color), inset 0 0 10px rgba(255, 27, 76, 0.7);
        }
        .right { grid-column: 3; grid-row: 2; }
        .backward { grid-column: 2; grid-row: 3; }

        .action-buttons-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 10;
        }

        .action-btn {
            width: 110px;
            height: 45px;
            color: var(--text-color);
            border: 2px solid;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-family: var(--font-primary);
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
            line-height: 1.2;
            padding: 5px;
            box-sizing: border-box;
            clip-path: polygon(0 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%);
        }

        .photo-btn {
            border-color: var(--success-glow-color);
            background: rgba(46, 255, 123, 0.1);
            text-shadow: 0 0 8px var(--success-glow-color);
        }
        .photo-btn:hover {
            background: rgba(46, 255, 123, 0.3);
            box-shadow: 0 0 15px var(--success-glow-color);
        }
        
        .yolo-btn {
            border-color: var(--secondary-glow-color);
            background: rgba(255, 0, 255, 0.1);
            text-shadow: 0 0 8px var(--secondary-glow-color);
        }
        .yolo-btn:hover {
            background: rgba(255, 0, 255, 0.3);
            box-shadow: 0 0 15px var(--secondary-glow-color);
        }
        .yolo-btn.active {
            border-color: var(--primary-glow-color);
            background: rgba(0, 229, 255, 0.3);
            color: #fff;
            text-shadow: 0 0 8px #fff;
        }

        .message, #status-message {
            order: 4;
            margin-top: 5px;
            font-size: 1rem;
            color: var(--primary-glow-color);
            text-shadow: 0 0 5px var(--primary-glow-color);
            height: 24px;
            text-align: center;
            min-height: 24px;
            font-family: var(--font-secondary);
            font-weight: 700;
        }
        #message-box { order: 4; }
        #status-message { order: 5; }

        #mqtt-results {
            order: 6;
            margin-top: 10px;
            width: 90%;
            max-width: 960px;
            background-color: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 15px;
            min-height: 50px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 0.9rem;
            color: var(--text-color);
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
            font-family: 'Courier New', Courier, monospace;
        }
        
        #mqtt-results::-webkit-scrollbar { width: 8px; }
        #mqtt-results::-webkit-scrollbar-track { background: transparent; }
        #mqtt-results::-webkit-scrollbar-thumb { background-color: var(--primary-glow-color); border-radius: 4px; }

        .mqtt-message {
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px dashed var(--panel-border);
            text-shadow: 0 0 2px rgba(255,255,255,0.5);
        }
        .mqtt-message:last-child { border-bottom: none; }

        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .video-wrapper { border-radius: 8px; }
            .controls-overlay { bottom: 10px; right: 10px; width: 150px; height: 150px; gap: 8px; }
            .control-btn { font-size: 1.6rem; border-radius: 8px; }
            .stop { font-size: 1.3rem; }
            .action-buttons-overlay { top: 10px; left: 10px; gap: 10px; }
            .action-btn { width: 100px; height: 40px; font-size: 0.8rem; }
            .message, #status-message, #mqtt-results { font-size: 0.9rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="corner-top-right"></div>
        <div class="corner-bottom-left"></div>

        <h1>Smart Car Control Interface</h1>

        <div class="target-display">
            <h2>MISSION TARGET</h2>
            <p id="target-name">{{ cargo }}</p>
        </div>
        
        <div class="video-wrapper">
            <div class="video-container">
                <img src="{{ url_for('video_feed') }}" class="video-stream" alt="Video Stream">
            </div>
            <div class="controls-overlay">
                <button class="control-btn forward" onmousedown="sendCommand('w')" onmouseup="sendCommand('o')">▲</button>
                <button class="control-btn left" onmousedown="sendCommand('a')" onmouseup="sendCommand('o')">◄</button>
                <button class="control-btn stop" onclick="sendCommand('o')">🛑</button>
                <button class="control-btn right" onmousedown="sendCommand('d')" onmouseup="sendCommand('o')">►</button>
                <button class="control-btn backward" onmousedown="sendCommand('s')" onmouseup="sendCommand('o')">▼</button>
            </div>
            <div class="action-buttons-overlay">
                <button class="action-btn photo-btn" onclick="takePhoto()">CAPTURE</button>
                <button id="yolo-toggle-btn" class="action-btn yolo-btn" onclick="toggleYolo()">AUTOPILOT OFF</button>
            </div>
        </div>
        <div id="message-box" class="message"></div>
        <div id="status-message" class="message">STATUS: STANDBY</div>
        <div id="mqtt-results"><p class="mqtt-message initial-message">System logs will be displayed here...</p></div>
    </div>

    <script>
        const messageBox = document.getElementById('message-box');
        const statusMessage = document.getElementById('status-message');
        const mqttResultsBox = document.getElementById('mqtt-results');
        const yoloBtn = document.getElementById('yolo-toggle-btn');
        const targetName = document.getElementById('target-name');

        function showMessage(msg) { messageBox.innerText = msg; setTimeout(() => { messageBox.innerText = ''; }, 3000); }
        function updateStatus(msg) { statusMessage.innerText = `STATUS: ${msg}`; }
        function addMqttResult(msg) {
            const initialMessage = mqttResultsBox.querySelector('.initial-message');
            if (initialMessage) {
                mqttResultsBox.innerHTML = '';
            }

            const p = document.createElement('p');
            p.classList.add('mqtt-message');
            p.innerText = `[${new Date().toLocaleTimeString()}] > ${msg}`;
            mqttResultsBox.prepend(p);
            while (mqttResultsBox.children.length > 10) { mqttResultsBox.removeChild(mqttResultsBox.lastChild); }
        }

        async function sendCommand(command) {
            updateStatus('Sending command...');
            try {
                const response = await fetch('/control', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });
                if (response.ok) { updateStatus(`Command sent: ${command}`); }
                else { const errorData = await response.json(); updateStatus(`Command failed: ${errorData.message}`); }
            } catch (error) { console.error('Error:', error); updateStatus('Command request failed!'); }
        }

        async function takePhoto() {
            showMessage('Taking photo...'); updateStatus('Capturing image...');
            try {
                const response = await fetch('/capture');
                const data = await response.json();
                if (response.ok) { showMessage(`Photo saved: ${data.file}`); updateStatus('Capture successful!'); }
                else { showMessage(`Capture failed: ${data.error}`); updateStatus('Capture failed!'); }
            } catch (error) { console.error('Error:', error); showMessage('Capture request failed!'); updateStatus('Capture request failed!'); }
        }
        
        async function toggleYolo() {
            updateStatus('Toggling Autopilot...');
            try {
                const response = await fetch('/toggle_detection', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    const isActive = data.detection_active;
                    yoloBtn.textContent = isActive ? 'AUTOPILOT ON' : 'AUTOPILOT OFF';
                    yoloBtn.classList.toggle('active', isActive);
                    updateStatus(`Autopilot: ${isActive ? 'Engaged' : 'Disengaged'}`);
                } else {
                    updateStatus(`Toggle failed: ${data.message}`);
                }
            } catch (error) {
                console.error('Error toggling Autopilot:', error);
                updateStatus('Autopilot toggle request error!');
            }
        }

        let lastKeyPressed = null;
        document.addEventListener('keydown', (event) => {
            const keyMap = { 'w': 'w', 's': 's', 'a': 'a', 'd': 'd' };
            if (keyMap[event.key] && !event.repeat) { sendCommand(keyMap[event.key]); lastKeyPressed = keyMap[event.key]; }
        });
        document.addEventListener('keyup', (event) => {
            const keyMap = { 'w': 'w', 's': 's', 'a': 'a', 'd': 'd' };
            if (keyMap[event.key] && lastKeyPressed === keyMap[event.key]) { sendCommand('o'); lastKeyPressed = null; }
        });

        const eventSource = new EventSource('/events');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'mqtt_result' || data.type === 'info' || data.type === 'error') { addMqttResult(data.message); }
            else if (data.type === 'status') { updateStatus(data.message); }
            else if (data.type === 'cargo_update') { targetName.innerText = data.cargo; }
        };
        eventSource.onerror = function(err) { console.error("EventSource failed:", err); updateStatus("Connection to server lost."); };
        
        document.addEventListener('DOMContentLoaded', () => { 
            updateStatus('Ready'); 
        });
    </script>
</body>
</html>
"""

# ==================== Helper Function for Photo Capture ====================
def _capture_photo_internal(picam_instance, photo_dir, frame_width, frame_height, target_fps):
    try:
        if not os.path.exists(photo_dir): os.makedirs(photo_dir)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(photo_dir, filename)

        current_video_config = picam_instance.create_video_configuration(main={"size": (frame_width, frame_height)}, controls={"FrameRate": target_fps})
        still_config = picam_instance.create_still_configuration()

        picam_instance.stop()
        picam_instance.configure(still_config)
        picam_instance.start()
        picam_instance.capture_file(filepath)
        picam_instance.stop()
        picam_instance.configure(current_video_config)
        picam_instance.start()
        print(f"Photo saved to {filepath}")


        return {"status": "success", "file": filename}
    except Exception as e:
        print(f"Photo capture failed: {e}")
        with sse_message_ready:
            sse_message_queue.append({"type": "error", "message": f"拍照失败: {e}"})
            sse_message_ready.notify_all()
        return {"status": "error", "message": str(e)}

# ==================== Detection Thread (MODIFIED) ====================
def detection_thread():
    """
    This thread runs in the background to perform YOLO detection and control the car.
    It reads frames from a queue, runs the model, and sends movement commands.
    """
    global latest_boxes, yolo_detection_active
    global cargo, my_cargo2, cargo_times
    print("Detection thread started.")
    
    frame_center_x = FRAME_WIDTH / 2
    last_command_time = 0
    command_interval = 2.0 # seconds, to prevent flooding the serial port
    pre_state = 0
    while True:
        with yolo_detection_lock:
            is_detection_active = yolo_detection_active

        if not is_detection_active:
            time.sleep(0.5) # Sleep when detection is off to save CPU
            continue

        try:
            # Wait for a frame to be available in the queue
            frame = detection_frame_queue[-1]
            # print('pick')
        except IndexError:
            # If no frame, stop the car and wait
            if ser and time.time() - last_command_time >= command_interval:
                ser.write(('o' + '\n').encode('utf-8'))
                last_command_time = time.time()
                print('test_stop')
            time.sleep(0.01)
            continue

        if yolo_model:
            # print('loop')
            response = ser.readline().decode().strip()
            # num = int(response)
            print("try to response")
            print(response)
            if response == '716': # change target
                print("Pick Done!")
                cargo = my_cargo2
                cargo_times += 1
                if cargo_times == 2:
                    cargo = 'null'
                    my_cargo2 = 'null'
                    cargo_times = 0
            try:
                # Run YOLO model
                results = yolo_model(frame, verbose=False)
                
                temp_boxes = []
                cargo_found = False
                
                # Assuming the largest detected "cell phone" is the target
                best_box = None
                max_area = 0

                for r in results:
                    for box in r.boxes:
                        cls = int(box.cls[0])
                        name = yolo_model.names[cls]
                        # Ensure the detected object is a 'cell phone' or your specific cargo name
                        # print('A:'+ cargo)
                        # cargo = 'banana' #调试
                        if name == cargo: #name == cargo
                        # if name == cargo:
                            print('B:' + cargo)
                            cargo_found = True
                            bbox = box.xyxy[0].tolist()
                            x1, y1, x2, y2 = bbox
                            area = (x2 - x1) * (y2 - y1)
                            # Find the largest detected cargo item
                            if area > max_area:
                                max_area = area
                                best_box = box
                            # best_box = box
                
                # --- Autonomous Control Logic ---
                if cargo == 'null':
                    if ser and time.time() - last_command_time > command_interval:
                        ser.write(('o' + '\n').encode('utf-8'))
                        print('no target')
                        last_command_time = time.time()
                elif cargo_found and best_box is not None:
                    print('yolo done')
                    # Append the best box for drawing on the stream
                    temp_boxes.append((best_box.xyxy[0], float(best_box.conf[0])))

                    # Get coordinates and calculate the center of the best box
                    bbox = best_box.xyxy[0].tolist()
                    x1, y1, x2, y2 = bbox
                    box_center_x = (x1 + x2) / 2
                    
                    # Calculate horizontal offset from the frame center
                    offset = box_center_x - frame_center_x

                    # Send commands based on the offset
                    if ser and time.time() - last_command_time > command_interval:
                        if abs(offset) > CENTER_TOLERANCE:
                            # Not centered, need to turn
                            if offset > 0: #4
                                pre_state = 4
                                # Cargo is to the right, turn right
                                ser.write(('d' + '\n').encode('utf-8'))
                                print('state:4')
                                print(f'Autopilot: Turning Right (Offset: {offset:.2f})')
                            else: #1
                                pre_state = 1
                                # Cargo is to the left, turn left
                                ser.write(('a' + '\n').encode('utf-8'))
                                print('state:1')
                                print(f'Autopilot: Turning Left (Offset: {offset:.2f})')
                        else:
                            # Centered, move forward
                            if offset > 0: #3
                                print('state:3')
                                if pre_state == 4:
                                    # ser.write(('d' + '\n').encode('utf-8'))
                                    ser.write(('w' + '\n').encode('utf-8'))
                                    # print(f'Autopilot: Turning Right (Offset: {offset:.2f})')
                                    print(f'Autopilot: Aligned. Moving Forward (Offset: {offset:.2f})')
                                    pre_state = 3
                                else:
                                    ser.write(('w' + '\n').encode('utf-8'))
                                    print(f'Autopilot: Aligned. Moving Forward (Offset: {offset:.2f})')
                                    pre_state = 3
                                    
                            else: #2
                                print('state:2')
                                if pre_state == 1:
                                    #ser.write(('a' + '\n').encode('utf-8'))
                                    ser.write(('w' + '\n').encode('utf-8'))
                                    #print(f'Autopilot: Turning Left (Offset: {offset:.2f})')
                                    print(f'Autopilot: Aligned. Moving Forward (Offset: {offset:.2f})')
                                    pre_state = 2
                                else:
                                    ser.write(('w' + '\n').encode('utf-8'))
                                    print(f'Autopilot: Aligned. Moving Forward (Offset: {offset:.2f})')
                                    pre_state = 2
                        last_command_time = time.time()

                else:
                    # No cargo detected, stop the car
                    if ser and time.time() - last_command_time > command_interval:
                        ser.write(('f' + '\n').encode('utf-8'))
                        print('Autopilot: No cargo detected. Searching.')
                        last_command_time = time.time()

                time.sleep(1.0)
                detection_frame_queue.popleft()

                # Update the global list of boxes for drawing
                with latest_boxes_lock:
                    latest_boxes = temp_boxes
            
            except Exception as e:
                print(f"Error during YOLO detection: {e}")
                # Stop the car in case of an error
                if ser: ser.write(('o' + '\n').encode('utf-8'))


# ==================== Camera Thread ====================
def camera_thread():
    """
    This thread continuously captures frames, sends them to the web stream,
    and periodically sends a frame to the detection thread.
    """
    global frame_buffer

    video_config = picam2.create_video_configuration(main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}, controls={"FrameRate": TARGET_FPS})
    picam2.configure(video_config)
    picam2.start()
    time.sleep(1)

    print("\nCamera thread started.")
    frame_counter = 0

    while True:
        # Capture frame
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_counter += 1

        # Periodically send a frame to the detection queue
        if frame_counter % DETECTION_FRAME_SKIP == 0:
            # Create a copy for the detection thread
            detection_frame = frame.copy()
            try:
                # Non-blocking put: if the queue is full, it won't wait
                if not detection_frame_queue:
                    print('provide new frame')
                    detection_frame_queue.append(detection_frame)
            except IndexError:
                pass # Queue is full, just skip this frame for detection

        # Get the latest detection boxes and draw them on the current frame
        with latest_boxes_lock:
            boxes_to_draw = latest_boxes
        
        if boxes_to_draw:
            for box_info in boxes_to_draw:
                # print('new_draw')
                box, conf = box_info
                x1, y1, x2, y2 = [int(i) for i in box]
                # IMPORTANT: Change 'cell phone' if your model uses a different name
                label = f"Cargo {conf:.2f}" 
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Calculate and draw the center point of the bounding box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)  # Red dot
        
        # Draw the center tolerance zone for visualization
        cv2.line(frame, (int(FRAME_WIDTH/2 - CENTER_TOLERANCE), 0), (int(FRAME_WIDTH/2 - CENTER_TOLERANCE), FRAME_HEIGHT), (255, 255, 0), 1)
        cv2.line(frame, (int(FRAME_WIDTH/2 + CENTER_TOLERANCE), 0), (int(FRAME_WIDTH/2 + CENTER_TOLERANCE), FRAME_HEIGHT), (255, 255, 0), 1)


        # Encode the frame for streaming
        ret, jpeg_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            with frame_ready:
                frame_buffer = jpeg_frame.tobytes()
                frame_ready.notify_all()
        
        time.sleep(1 / TARGET_FPS)

# ==================== Keyboard Control Thread (MODIFIED) ====================
def keyboard_control_thread():
    if sys.platform == "win32":
        print("Keyboard control thread not supported on Windows.")
        return

    original_settings = termios.tcgetattr(sys.stdin)
    atexit.register(lambda: termios.tcsetattr(sys.stdin, termios.TCSANOW, original_settings))
    tty.setcbreak(sys.stdin.fileno())

    print("\nKeyboard direct control mode started.")
    print("Press 'w', 'a', 's', 'd' to control. Release to stop. Ctrl+C to exit.")

    last_movement_char = None
    try:
        while True:
            if yolo_detection_active:
                continue
            # *** ADDED CHECK: Only allow keyboard control if autopilot is OFF ***
            if yolo_detection_active:
                # If autopilot becomes active, ensure the car stops from manual control
                if last_movement_char is not None:
                    if ser: ser.write('o\n'.encode('utf-8'))
                    print("Autopilot activated, stopping manual control.")
                    last_movement_char = None
                time.sleep(0.1) # Sleep to prevent busy-waiting
                continue

            if select.select([sys.stdin], [], [], 0.05)[0]:
                char = sys.stdin.read(1)
                if ser:
                    if char in ['w', 's']:
                        if char != last_movement_char:
                            ser.write((char + '\n').encode('utf-8'))
                            print(f"Sent: {char}")
                            last_movement_char = char
                    elif char in ['a', 'd', 'f', 'g', 'o']:
                         ser.write((char + '\n').encode('utf-8'))
                         print(f"Sent: {char}")
                         if char == 'o': last_movement_char = None
            else:
                if last_movement_char:
                    if ser: ser.write('o\n'.encode('utf-8'))
                    print("Sent: o (Key release stop)")
                    last_movement_char = None
    except Exception as e:
        print(f"Keyboard control thread error: {e}")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSANOW, original_settings)


# ==================== Flask Routes ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_frames():
    global frame_buffer
    while True:
        with frame_ready:
            frame_ready.wait()
            if frame_buffer:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_buffer + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture', methods=['GET'])
def capture_photo():
    result = _capture_photo_internal(picam2, PHOTO_DIRECTORY, FRAME_WIDTH, FRAME_HEIGHT, TARGET_FPS)
    if result["status"] == "success": return jsonify(result)
    else: return jsonify(result), 500

@app.route('/control', methods=['POST'])
def control_car():
    data = request.get_json()
    command = data.get('command')
    
    # *** ADDED CHECK: Do not allow web control if autopilot is ON ***
    if yolo_detection_active:
        return jsonify({"status": "error", "message": "Cannot send command, Autopilot is active."}), 403

    if command and ser:
        try:
            ser.write((command + '\n').encode('utf-8'))
            return jsonify({"status": "success", "command": command})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    elif not ser:
        return jsonify({"status": "error", "message": "Serial port not available"}), 500
    return jsonify({"status": "error", "message": "No command received"}), 400

@app.route('/events')
def sse_events():
    def generate_events():
        while True:
            with sse_message_ready:
                if sse_message_queue:
                    message = sse_message_queue.popleft()
                    yield f"data: {json.dumps(message)}\n\n"
                else:
                    sse_message_ready.wait()
                    if sse_message_queue:
                        message = sse_message_queue.popleft()
                        yield f"data: {json.dumps(message)}\n\n"
            time.sleep(0.1)

    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/toggle_detection', methods=['POST'])
def toggle_detection():
    global yolo_detection_active
    with yolo_detection_lock:
        yolo_detection_active = not yolo_detection_active
        current_status = yolo_detection_active
        # When turning off autopilot, send a stop command to be safe
        if not current_status and ser:
            ser.write(('o' + '\n').encode('utf-8'))
            print("Autopilot disabled. Sending stop command.")

    status_str = "enabled" if current_status else "disabled"
    print(f"Autopilot has been {status_str}.")
    with sse_message_ready:
        sse_message_queue.append({"type": "status", "message": f"自动驾驶已{'开启' if current_status else '关闭'}."})
        sse_message_ready.notify_all()
    return jsonify({"status": "success", "detection_active": current_status})


# ==================== Program Entry Point ====================
if __name__ == '__main__':
    try:
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print("YOLO model loaded successfully.")
    except Exception as e:
        print(f"Fatal: Error loading YOLO model: {e}")
        sys.exit(1)

    mqtt_client = setup_mqtt_client(MQTT_BROKER_HOSTNAME)
    # print(cargo)
    if mqtt_client is None:
        print("Warning: MQTT client could not be initialized.")
        with sse_message_ready:
            sse_message_queue.append({"type": "error", "message": "MQTT客户端未初始化."})
            sse_message_ready.notify_all()

    # Start all threads
    cam_thread = threading.Thread(target=camera_thread, daemon=True)
    det_thread = threading.Thread(target=detection_thread, daemon=True)
    cam_thread.start()
    det_thread.start()

    if sys.platform != "win32":
        key_thread = threading.Thread(target=keyboard_control_thread, daemon=True)
        key_thread.start()

    print("Starting Flask server... Please visit http://<Your Raspberry Pi IP>:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
