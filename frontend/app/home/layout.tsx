import { AppSidebar } from "@/components/app-sidebar";
import { ProtectedRoute } from "@/components/protected-route";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

const HomeLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <ProtectedRoute>
        <main>{children}</main>
        </ProtectedRoute>
      </SidebarInset>
    </SidebarProvider>
  );
};

export default HomeLayout;
