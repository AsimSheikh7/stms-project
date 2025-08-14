from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback
import datetime

# traci will be imported/used by simulation.start_simulation
import traci as traci_module

from simulation import simulate_sensors, start_simulation, set_signal_state
from models import db, User, Simulation, TrafficData
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# SQLite DB file
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# globals
traci = None
sensor_generator = None
current_simulation_id = None


def ensure_db_and_default_user():
    """Create tables and default admin user (email='admin', password='admin') if missing."""
    with app.app_context():
        db.create_all()
        admin_email = "admin"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                password_hash=generate_password_hash("admin"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user: admin/admin (email field = 'admin').")
        else:
            print("Default admin user already exists.")


def restart_simulation():
    """
    Closes any existing SUMO connection and starts a new one.
    Also creates a Simulation DB row and stores current_simulation_id.
    """
    global traci, sensor_generator, current_simulation_id

    try:
        if traci:
            try:
                traci_module.close(False)
            except Exception:
                # ignore any close errors
                pass
            traci = None
    except Exception:
        pass

    traci = start_simulation()
    if not traci:
        return False

    sensor_generator = simulate_sensors()

    # Create a simulation record in DB
    with app.app_context():
        sim = Simulation(start_time=datetime.datetime.utcnow())
        db.session.add(sim)
        db.session.commit()
        current_simulation_id = sim.id
        print(f"Started new simulation id={current_simulation_id}")

    return True


def end_current_simulation():
    """Set end_time for current simulation in DB."""
    global current_simulation_id
    with app.app_context():
        if current_simulation_id is not None:
            sim = Simulation.query.get(current_simulation_id)
            if sim and sim.end_time is None:
                sim.end_time = datetime.datetime.utcnow()
                db.session.commit()
                print(f"Marked simulation id={current_simulation_id} ended at {sim.end_time}")
    current_simulation_id = None


def store_sensor_readings(sensors):
    """
    sensors returned from simulate_sensors() contains:
      - per-lane counts (sensors['north_in_0'], etc.)
      - sensors['queue_length'][lane]
      - sensors['avg_speed'][lane]
      - sensors['emergency']
    We'll insert a row per lane with the current simulation id.
    """
    global current_simulation_id
    if current_simulation_id is None:
        return

    timestamp = datetime.datetime.utcnow()
    lane_keys = [k for k in sensors.keys() if isinstance(k, str) and k.endswith(("_in_0", "_in_1"))]

    with app.app_context():
        rows = []
        for lane in lane_keys:
            try:
                vehicle_count = int(round(float(sensors.get(lane, 0))))
            except Exception:
                vehicle_count = 0
            try:
                queue_length = int(round(float(sensors.get("queue_length", {}).get(lane, 0))))
            except Exception:
                queue_length = 0
            try:
                avg_speed = float(sensors.get("avg_speed", {}).get(lane, 0.0))
            except Exception:
                avg_speed = 0.0

            td = TrafficData(
                simulation_id=current_simulation_id,
                timestamp=timestamp,
                lane=lane,
                vehicle_count=vehicle_count,
                queue_length=queue_length,
                avg_speed=avg_speed,
                emergency=bool(sensors.get("emergency", False)),
            )
            rows.append(td)
        if rows:
            db.session.bulk_save_objects(rows)
            db.session.commit()


@app.route("/api/sensors", methods=["GET"])
def sensors():
    global traci, sensor_generator
    try:
        # Start or restart if no simulation running
        if not traci or traci.simulation.getMinExpectedNumber() == 0:
            if not restart_simulation():
                return jsonify({"error": "Failed to start SUMO simulation"}), 500

        sensors = next(sensor_generator)  # may raise StopIteration if sim ended
        # store readings to DB (one row per lane)
        try:
            store_sensor_readings(sensors)
        except Exception as e:
            print(f"Warning: failed to store sensor readings: {e}")

        return jsonify(sensors)

    except StopIteration:
        # simulation ended; mark end time and restart
        end_current_simulation()
        if restart_simulation():
            try:
                sensors = next(sensor_generator)
                store_sensor_readings(sensors)
                return jsonify(sensors)
            except Exception as e:
                print(f"Error after restarting simulation: {e}\n{traceback.format_exc()}")
                return jsonify({"error": "Failed after restarting SUMO simulation"}), 500
        else:
            return jsonify({"error": "Failed to restart SUMO simulation"}), 500

    except Exception as e:
        print(f"Error in /api/sensors: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/signal", methods=["POST"])
def signal():
    global traci, sensor_generator
    try:
        if not traci or traci.simulation.getMinExpectedNumber() == 0:
            if not restart_simulation():
                return jsonify({"error": "Failed to start SUMO simulation"}), 500

        data = request.json or {}
        mode = data.get("mode", "auto")
        sensors = {"mode": mode}
        if mode == "manual":
            sensors["lane"] = data.get("lane")
            sensors["state"] = data.get("state")
            sensors["emergency"] = False
            sensors["emergency_lane"] = None
        else:
            # include latest sensor data (this also stores to DB in /api/sensors)
            sensors.update(next(sensor_generator))

        set_signal_state(traci, "junction1", sensors)
        return jsonify({"status": "Signal updated", "mode": mode})
    except StopIteration:
        # simulation ended
        end_current_simulation()
        if restart_simulation():
            return jsonify({"status": "Simulation restarted due to end"})
        else:
            return jsonify({"error": "Failed to restart SUMO simulation"}), 500
    except Exception as e:
        print(f"Error in /api/signal: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/simulations", methods=["GET"])
def list_simulations():
    """Return list of simulations (id, start_time, end_time)."""
    with app.app_context():
        sims = Simulation.query.order_by(Simulation.id.desc()).limit(50).all()
        return jsonify([
            {"id": s.id, "start_time": s.start_time.isoformat(), "end_time": s.end_time.isoformat() if s.end_time else None}
            for s in sims
        ])


@app.route("/api/traffic/<int:simulation_id>", methods=["GET"])
def get_traffic_for_sim(simulation_id):
    """Return latest traffic rows for a simulation (paginated simple)."""
    with app.app_context():
        rows = TrafficData.query.filter_by(simulation_id=simulation_id).order_by(TrafficData.timestamp.asc()).limit(2000).all()
        return jsonify([
            {
                "timestamp": r.timestamp.isoformat(),
                "lane": r.lane,
                "vehicle_count": r.vehicle_count,
                "queue_length": r.queue_length,
                "avg_speed": r.avg_speed,
                "emergency": r.emergency
            } for r in rows
        ])


if __name__ == "__main__":
    ensure_db_and_default_user()
    app.run(debug=True, port=5000)
