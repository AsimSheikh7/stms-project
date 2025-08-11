from flask import Flask, jsonify, request
from flask_cors import CORS
from simulation import simulate_sensors, start_simulation, get_sensor_data, set_signal_state
import traceback

app = Flask(__name__)
CORS(app)
traci = None
sensor_generator = None

@app.route('/api/sensors', methods=['GET'])
def sensors():
    global traci, sensor_generator
    if not traci or traci.simulation.getMinExpectedNumber() == 0:
        traci = start_simulation()
        if traci:
            sensor_generator = simulate_sensors()
        else:
            return jsonify({"error": "Failed to start SUMO simulation"}), 500
    try:
        return jsonify(next(sensor_generator))
    except StopIteration:
        traci = start_simulation()
        if traci:
            sensor_generator = simulate_sensors()
            return jsonify(next(sensor_generator))
        else:
            return jsonify({"error": "Failed to restart SUMO simulation"}), 500
    except Exception as e:
        print(f"Error in /api/sensors: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/signal', methods=['POST'])
def signal():
    global traci, sensor_generator
    if not traci or traci.simulation.getMinExpectedNumber() == 0:
        traci = start_simulation()
        if traci:
            sensor_generator = simulate_sensors()
        else:
            return jsonify({"error": "Failed to start SUMO simulation"}), 500
    try:
        data = request.json or {}
        mode = data.get('mode', 'auto')
        sensors = {"mode": mode}
        if mode == 'manual':
            sensors['lane'] = data.get('lane')
            sensors['state'] = data.get('state')
            sensors['emergency'] = False
            sensors['emergency_lane'] = None
        else:
            # For auto mode, include latest sensor data
            sensors.update(next(sensor_generator))
        set_signal_state(traci, "junction1", sensors)
        return jsonify({"status": "Signal updated", "mode": mode})
    except Exception as e:
        print(f"Error in /api/signal: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)