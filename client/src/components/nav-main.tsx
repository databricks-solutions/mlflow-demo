"use client";

import { type LucideIcon } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { getViewTypeFromPath, getPathFromViewType, ViewType } from "@/routes";

export function NavMain({
  items,
  label = "Features",
}: {
  items: {
    title: string;
    value: string;
    icon?: LucideIcon;
  }[];
  label?: string;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentView = getViewTypeFromPath(location.pathname);
  return (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton
              onClick={() => {
                window.scrollTo(0, 0);
                navigate(getPathFromViewType(item.value as ViewType));
              }}
              isActive={currentView === item.value}
            >
              {item.icon && <item.icon />}
              <span>{item.title}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
