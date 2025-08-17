"use client";

import * as React from "react";
import { LayoutDashboard, TrafficCone, Users } from "lucide-react";
import { NavMain } from "@/components/nav-main";
import { NavUser } from "@/components/nav-user";
import AppLogo from "@/public/app_logo.png";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenuButton,
  SidebarRail,
} from "@/components/ui/sidebar";
import Image from "next/image";
import { useAuth } from "@/components/providers/auth-provider";
import { usePathname } from "next/navigation";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const userDetails = useAuth();
 

  // Nav data
  const data = {
    user: {
      name: userDetails.user?.username || "",
      email: userDetails.user?.email || "",
      avatar: "/avatars/shadcn.jpg",
    },
    navMain: [
      {
        title: "Dashboard",
        url: "/home/dashboard",
        icon: LayoutDashboard,
  
      },
      {
        title: "Traffic Management",
        url: "/home/traffic-management",
        icon: TrafficCone,
      },
      {
        title: "User Management",
        url: "/home/user-management",
        icon: Users,
      },
    ],
  };

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenuButton
          size="lg"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground mt-2"
        >
          <div className="flex flex-row gap-1 items-center">
            <Image src={AppLogo} alt="STMS logo" height={40} width={40} />
            <div className="flex flex-col">
              <h1 className="text-base">STMS</h1>
              <h1 className="text-xs">(Smart Traffic Mgmt. System)</h1>
            </div>
          </div>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} currentPath={pathname} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
