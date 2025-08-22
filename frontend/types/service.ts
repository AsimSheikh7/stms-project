export interface UserEntity {
  id: number;
  username: string;
  email: string;
  role: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: string;
}

export interface DashboardSummary {
  global: {
    total_simulations: number;
    total_vehicles: number;
    avg_queue_length: number;
    emergencies_handled: number;
    current_simulation: {
      id: number;
      start_time: string;
    } | null;
  };
  recent_simulations: SimulationStats[];
}

export interface SimulationStats {
  id: number;
  start_time: string;
  end_time: string | null;
  total_vehicles: number;
  avg_queue_length: number;
  emergencies: number;
}

export interface SimulationEntity {
  id: number;
  start_time: string;
  end_time: string | null;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}
