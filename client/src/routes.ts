export type ViewType =
  | "chat"
  | "email"
  | "demo-overview"
  | "step1-tracing"
  | "step2-evaluation"
  | "step3-improvement"
  | "step4-kpis"
  | "step5-monitoring"
  | "step6-human-review"
  | "step5-prompt-registry";

export const routes: Record<ViewType, string> = {
  "demo-overview": "/",
  chat: "/chat",
  email: "/email",
  "step1-tracing": "/tracing",
  "step2-evaluation": "/evaluation",
  "step3-improvement": "/improvement",
  "step4-kpis": "/kpis",
  "step5-monitoring": "/monitoring",
  "step6-human-review": "/human-review",
  "step5-prompt-registry": "/prompt-registry",
};

// Reverse mapping for getting ViewType from path
export const pathToViewType: Record<string, ViewType> = Object.entries(
  routes,
).reduce(
  (acc, [viewType, path]) => {
    acc[path] = viewType as ViewType;
    return acc;
  },
  {} as Record<string, ViewType>,
);

export const getViewTypeFromPath = (pathname: string): ViewType => {
  return pathToViewType[pathname] || "demo-overview";
};

export const getPathFromViewType = (viewType: ViewType): string => {
  return routes[viewType] || "/";
};
