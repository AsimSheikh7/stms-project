import traci
import random

def start_simulation():
    # Start SUMO in non-GUI mode for TraCI control
    traci.start(["sumo", "-c", "../sumo/network.sumocfg"])
    return traci

def simulate_sensors():
    # Map your edge IDs to lanes (each edge has 2 lanes due to numLanes="2")
    lanes = ["north_in_0", "north_in_1", "south_in_0", "south_in_1", 
             "east_in_0", "east_in_1", "west_in_0", "west_in_1"]
    sensors = {lane: 0 for lane in lanes}
    sensors["emergency"] = False
    sensors["emergency_lane"] = None
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        # Count vehicles per lane
        for lane in lanes:
            sensors[lane] = traci.lane.getLastStepVehicleNumber(lane)
        # Detect emergency vehicles
        vehicle_ids = traci.vehicle.getIDList()
        sensors["emergency"] = any(traci.vehicle.getVehicleClass(vid) == "emergency" for vid in vehicle_ids)
        if sensors["emergency"]:
            for vid in vehicle_ids:
                if traci.vehicle.getVehicleClass(vid) == "emergency":
                    sensors["emergency_lane"] = traci.vehicle.getLaneID(vid)
                    break
        else:
            sensors["emergency_lane"] = None
        yield sensors
    traci.close()

def get_sensor_data():
    return next(simulate_sensors())