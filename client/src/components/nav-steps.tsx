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

interface StepItem {
  title: string;
  value: string;
  icon: LucideIcon;
  description: string;
}

interface NavStepsProps {
  items: StepItem[];
  label?: string;
}

export function NavSteps({ items, label = "MLflow Demos" }: NavStepsProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentView = getViewTypeFromPath(location.pathname);
  return (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.value}>
            <SidebarMenuButton asChild isActive={currentView === item.value}>
              <button
                className="w-full text-left flex items-start gap-2 p-2 min-h-fit"
                onClick={() => {
                  window.scrollTo(0, 0);
                  navigate(getPathFromViewType(item.value as ViewType));
                }}
              >
                <item.icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-sm font-medium truncate">
                    {item.title}
                  </span>
                  <span className="text-xs text-muted-foreground leading-tight">
                    {item.description}
                  </span>
                </div>
              </button>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
