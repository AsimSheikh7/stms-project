import { API_BASE_URL } from "@/lib/constants";
import { ApiResponse, SensorsResponse, SignalResponse } from "@/types/service";

export class TrafficManagementService {
  private static getAuthHeaders(token: string) {
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  static async getSensors(
    token: string
  ): Promise<ApiResponse<SensorsResponse>> {
    try {
      const response = await fetch(`${API_BASE_URL}/sensors`, {
        method: "GET",
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errText}`);
      }

      const data: SensorsResponse = await response.json();
      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : "Failed to fetch sensors",
      };
    }
  }
  static async updateSignal(
    token: string,
    body: { mode: "auto" | "manual"; lane?: string; state?: string }
  ): Promise<ApiResponse<SignalResponse>> {
    try {
      const response = await fetch(`${API_BASE_URL}/signal`, {
        method: "POST",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errText}`);
      }

      const data: SignalResponse = await response.json();
      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : "Failed to update signal",
      };
    }
  }
}
