from flask import Flask, jsonify
from flask_cors import CORS
from simulation import start_simulation, get_sensor_data

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
traci = None

@app.route('/api/sensors', methods=['GET'])
def sensors():
    global traci
    if not traci:
        traci = start_simulation()
    return jsonify(get_sensor_data())

if __name__ == '__main__':
    app.run(debug=True, port=5000)