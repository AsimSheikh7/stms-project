"use client";
import { useEffect, useState } from "react";
import { TrafficManagementService } from "@/service/traffic-management.service";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";
import { SensorsResponse } from "@/types/service";
import { toast } from "sonner";
import { useAuthStore } from "@/store/auth.store";
import { laneLabels } from "@/lib/constants";

export default function Page() {
  const token = useAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [sensors, setSensors] = useState<SensorsResponse | null>(null);
  const [mode, setMode] = useState<"auto" | "manual">("auto");
  const [lastEmergency, setLastEmergency] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    const fetchSensors = async () => {
      const { data, error } = await TrafficManagementService.getSensors(
        token ?? ""
      );
      if (error) {
        console.error(error);
        return;
      }
      if (data) {
        setSensors(data);

        // Emergency detection
        if (data.emergency && !lastEmergency) {
          toast.error(
            `Emergency vehicle detected on ${
              data.emergency_lane !== null && data.emergency_lane !== undefined
                ? laneLabels[data.emergency_lane] ?? data.emergency_lane
                : "unknown lane"
            }`
          );
          // play siren audio
          const audio = new Audio("/siren.mp3");
          audio.play().catch(() => {});
        }
        setLastEmergency(data.emergency);
      }
    };
    fetchSensors();
    // eslint-disable-next-line prefer-const
    timer = setInterval(fetchSensors, 100);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toast, lastEmergency]);

  const handleModeChange = async (checked: boolean) => {
    const newMode: "auto" | "manual" = checked ? "manual" : "auto";
    setMode(newMode);
    setLoading(true);
    const { error } = await TrafficManagementService.updateSignal(
      token ?? "",
      {
        mode: newMode,
      }
    );
    setLoading(false);
    if (error) {
      console.error(error);
    } else {
      toast.success(`Mode changed to ${newMode}`);
    }
  };

  const updateLaneSignal = async (lane: string, state: string) => {
    setLoading(true);
    const { error } = await TrafficManagementService.updateSignal(token ?? "", {
      mode: "manual",
      lane,
      state,
    });
    setLoading(false);
    if (error) {
      console.error(error);
    } else {
      toast.success(`Signal for ${lane} set to ${state}`);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Traffic Management
          </h1>
          <p className="text-muted-foreground">
            View and manage incoming traffic in realtime.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm">Auto</span>
          <Switch
            checked={mode === "manual"}
            onCheckedChange={handleModeChange}
            disabled={loading}
          />
          <span className="text-sm">Manual</span>
        </div>
      </div>

      {/* Junction Map Card */}
      <Card>
        <CardHeader>
          <CardTitle>Junction Map</CardTitle>
        </CardHeader>
        <CardContent>
          {!sensors ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {["north_in_0", "south_in_0", "east_in_0", "west_in_0"].map(
                (lane) => (
                  <div
                    key={lane}
                    className="rounded-xl border p-4 shadow-sm bg-card"
                  >
                    <h3 className="font-semibold capitalize">{laneLabels[lane] ?? lane}</h3>
                    <p className="text-sm">
                      Vehicles: {sensors[lane] as number}
                    </p>
                    <p className="text-sm">
                      Queue: {sensors.queue_length?.[lane] ?? 0}
                    </p>
                    <p className="text-sm">
                      Avg Speed: {sensors.avg_speed?.[lane] ?? 0} km/h
                    </p>
                    {mode === "manual" && (
                      <div className="flex gap-2 mt-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateLaneSignal(lane, "G")}
                        >
                          Green
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateLaneSignal(lane, "R")}
                        >
                          Red
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateLaneSignal(lane, "Y")}
                        >
                          Yellow
                        </Button>
                      </div>
                    )}
                  </div>
                )
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
