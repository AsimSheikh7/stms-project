import { API_BASE_URL } from "@/lib/constants";
import { ApiResponse, DashboardSummary, SimulationEntity } from "@/types/service";


export class DashboardService {
  private static getAuthHeaders(token: string) {
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  static async getSummary(token: string): Promise<ApiResponse<DashboardSummary>> {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/summary`, {
        method: "GET",
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data: DashboardSummary = await response.json();
      return { data };
    } catch (error) {
      console.error("Error fetching dashboard summary:", error);
      return {
        error: error instanceof Error ? error.message : "Failed to fetch summary",
      };
    }
  }

  static async getSimulations(token: string): Promise<ApiResponse<SimulationEntity[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/simulations`, {
        method: "GET",
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data: SimulationEntity[] = await response.json();
      return { data };
    } catch (error) {
      console.error("Error fetching simulations:", error);
      return {
        error: error instanceof Error ? error.message : "Failed to fetch simulations",
      };
    }
  }
}
