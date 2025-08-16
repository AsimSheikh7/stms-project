import { ProtectedRoute } from "@/components/protected-route";
import { ThemeSwitcher } from "@/components/theme-switcher";

export default function Home() {
  return (
    <div>
      <ProtectedRoute>
        <ThemeSwitcher />
      </ProtectedRoute>
    </div>
  );
}
