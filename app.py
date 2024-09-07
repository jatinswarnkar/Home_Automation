from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import smtplib
import threading
import time

app = Flask(__name__)

# Global variables to store sensor data
sensors = {
    'motion': False,
    'gas_leakage': False,
    'gas_value': 0,
    'temperature': 22,
    'humidity': 50,
    'door_status': 'closed'
}

# MQTT setup
mqtt_client = mqtt.Client()
mqtt_broker = 'localhost'
mqtt_port = 1883

# Email setup
smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = "jatinswarnkar04@gmail.com"
sender_password = "stckysaxmioqpeuh"  # Consider using environment variables for sensitive data

def send_email(subject, body):
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(sender_email, sender_email, message)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("/esp8266/motion")
    client.subscribe("/esp8266/gasvalue")
    # Uncomment if you add temperature sensor
    # client.subscribe("/esp8266/temperature")

def on_message(client, userdata, message):
    global sensors
    print(f"Received message {message.payload} on topic {message.topic}")
    
    if message.topic == "/esp8266/motion":
        sensors['motion'] = bool(int(message.payload))
        if sensors['motion']:
            send_email("Motion Alert", "Motion detected!")

    elif message.topic == "/esp8266/gasvalue":
        gas_value = float(message.payload)
        sensors['gas_value'] = gas_value
        sensors['gas_leakage'] = gas_value > 50.00
        if sensors['gas_leakage']:
            send_email("Gas Leakage Alert", f"Gas leakage detected! Value: {gas_value}")

    # Uncomment if you add temperature sensor
    # elif message.topic == "/esp8266/temperature":
    #     sensors['temperature'] = float(message.payload)
    #     if sensors['temperature'] > 50.00:
    #         send_email("Fire Alert", f"High temperature detected! Value: {sensors['temperature']}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def mqtt_loop():
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)
    mqtt_client.loop_forever()

# Start MQTT client in a separate thread
mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
mqtt_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_sensor_data')
def get_sensor_data():
    return jsonify(sensors)

@app.route('/toggle_device/<device>')
def toggle_device(device):
    # Simulate toggling a device (e.g., lights, AC)
    status = 'on' if device not in sensors else 'off' if sensors[device] else 'on'
    sensors[device] = status == 'on'
    return jsonify({'device': device, 'status': status})

@app.route('/get_energy_usage')
def get_energy_usage():
    # This is still simulated - you might want to implement real energy monitoring
    return jsonify({
        'daily': 15.5,
        'weekly': 80.2,
        'monthly': 320.7
    })

@app.route('/get_security_log')
def get_security_log():
    # In a real application, you'd maintain an actual log
    events = []
    if sensors['motion']:
        events.append(f"Motion detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if sensors['gas_leakage']:
        events.append(f"Gas leakage detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return jsonify({'log': events})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)