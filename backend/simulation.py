import traci
import random
import os

def start_simulation():
    try:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sumo/network.sumocfg"))
        if not os.path.exists(config_path):
            print(f"Error: SUMO config file not found at {config_path}")
            return None
        traci.start(["sumo-gui", "-c", config_path])
        print("SUMO simulation started successfully")
        return traci
    except traci.exceptions.TraCIException as e:
        print(f"Failed to start SUMO: {e}")
        return None


def set_signal_state(traci, junction_id, sensors):
    if not traci:
        return

    # Valid signal states from tlLogic in network.net.xml
    NORTH_SOUTH_GREEN = "GGGggrrrrrGGGggrrrrr"
    EAST_WEST_GREEN = "rrrrrGGGggrrrrrGGGgg"
    YELLOW_TRANSITION = "yyyyyrrrrryyyyyrrrrr"

    # Track last green direction and time to enforce fair cycling
    if not hasattr(set_signal_state, "last_green"):
        set_signal_state.last_green = None
        set_signal_state.green_start_time = 0
        set_signal_state.min_green_time = 10
        set_signal_state.emergency_active = False
        set_signal_state.emergency_direction = None

    current_time = traci.simulation.getTime()

    # --- Emergency Priority ---
    if sensors.get("emergency") or set_signal_state.emergency_active:
        if sensors.get("emergency"):
            set_signal_state.emergency_active = True
            if "north_in" in sensors["emergency_lane"] or "south_in" in sensors["emergency_lane"]:
                traci.trafficlight.setRedYellowGreenState(junction_id, NORTH_SOUTH_GREEN)
                set_signal_state.emergency_direction = "north_south"
            elif "east_in" in sensors["emergency_lane"] or "west_in" in sensors["emergency_lane"]:
                traci.trafficlight.setRedYellowGreenState(junction_id, EAST_WEST_GREEN)
                set_signal_state.emergency_direction = "east_west"
            set_signal_state.green_start_time = current_time

        # Keep emergency green until vehicle is gone
        if not any(traci.vehicle.getVehicleClass(v) == "emergency" for v in traci.vehicle.getIDList()):
            set_signal_state.emergency_active = False
            set_signal_state.emergency_direction = None

        return  # Skip normal logic while in emergency mode

    # --- Manual Mode ---
    if sensors.get("mode") == "manual":
        lane = sensors.get("lane")
        state = sensors.get("state")
        if lane in ["north_in_0", "north_in_1", "south_in_0", "south_in_1"] and state == "green":
            traci.trafficlight.setRedYellowGreenState(junction_id, NORTH_SOUTH_GREEN)
            set_signal_state.last_green = "north_south"
        elif lane in ["east_in_0", "east_in_1", "west_in_0", "west_in_1"] and state == "green":
            traci.trafficlight.setRedYellowGreenState(junction_id, EAST_WEST_GREEN)
            set_signal_state.last_green = "east_west"
        return

    # --- Auto Mode ---
    lane_counts = {lane: count for lane, count in sensors.items() if lane not in ["emergency", "emergency_lane", "mode", "lane", "state"]}
    if not lane_counts:
        return

    if current_time - set_signal_state.green_start_time >= set_signal_state.min_green_time:
        north_south_count = sum(lane_counts[l] for l in ["north_in_0", "north_in_1", "south_in_0", "south_in_1"])
        east_west_count = sum(lane_counts[l] for l in ["east_in_0", "east_in_1", "west_in_0", "west_in_1"])

        if set_signal_state.last_green == "north_south" and east_west_count > 0:
            traci.trafficlight.setRedYellowGreenState(junction_id, YELLOW_TRANSITION)
            traci.simulationStep()
            traci.trafficlight.setRedYellowGreenState(junction_id, EAST_WEST_GREEN)
            set_signal_state.last_green = "east_west"
        elif set_signal_state.last_green == "east_west" and north_south_count > 0:
            traci.trafficlight.setRedYellowGreenState(junction_id, YELLOW_TRANSITION)
            traci.simulationStep()
            traci.trafficlight.setRedYellowGreenState(junction_id, NORTH_SOUTH_GREEN)
            set_signal_state.last_green = "north_south"
        elif north_south_count >= east_west_count:
            traci.trafficlight.setRedYellowGreenState(junction_id, NORTH_SOUTH_GREEN)
            set_signal_state.last_green = "north_south"
        else:
            traci.trafficlight.setRedYellowGreenState(junction_id, EAST_WEST_GREEN)
            set_signal_state.last_green = "east_west"

        set_signal_state.green_start_time = current_time


def simulate_sensors():
    lanes = ["north_in_0", "north_in_1", "south_in_0", "south_in_1",
             "east_in_0", "east_in_1", "west_in_0", "west_in_1"]

    sensors = {lane: 0 for lane in lanes}
    sensors["emergency"] = False
    sensors["emergency_lane"] = None
    sensors["mode"] = "auto"  # default to auto

    junction_id = "junction1"

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # Collect lane counts
        for lane in lanes:
            sensors[lane] = traci.lane.getLastStepVehicleNumber(lane)

        # Detect emergency vehicles
        vehicle_ids = traci.vehicle.getIDList()
        sensors["emergency"] = any(traci.vehicle.getVehicleClass(v) == "emergency" for v in vehicle_ids)
        if sensors["emergency"]:
            for v in vehicle_ids:
                if traci.vehicle.getVehicleClass(v) == "emergency":
                    sensors["emergency_lane"] = traci.vehicle.getLaneID(v)
                    break
        else:
            sensors["emergency_lane"] = None

        # Update signals every step
        set_signal_state(traci, junction_id, sensors)

        yield sensors

    traci.close()


def get_sensor_data():
    return next(simulate_sensors())
