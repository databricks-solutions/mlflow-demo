import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { FileText, Database, Activity } from "lucide-react";

interface CustomerDataRetrieverProps {
  customerData: any;
  isLoading?: boolean;
  retrievalStatus?: "success" | "loading" | "error";
  dataSource?: string;
}

export function CustomerDataRetriever({
  customerData,
  isLoading = false,
  retrievalStatus = "success",
  dataSource = "MLflow JSONL Data File",
}: CustomerDataRetrieverProps) {
  if (isLoading || !customerData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 animate-spin text-muted-foreground" />
            Loading Customer Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-muted-foreground">
                Retrieving data via MLflow RETRIEVER span...
              </span>
            </div>

            {/* Loading skeleton */}
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded w-3/4 animate-pulse"></div>
              <div className="h-4 bg-muted rounded w-1/2 animate-pulse"></div>
              <div className="h-4 bg-muted rounded w-2/3 animate-pulse"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          Customer Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Customer Overview */}
        <div className="grid grid-cols-1 gap-3">
          <div>
            <Label className="text-sm font-medium">Company</Label>
            <p className="text-sm font-semibold text-foreground">
              {customerData.account?.name}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground">Industry</Label>
              <p className="text-sm">{customerData.account?.industry}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Size</Label>
              <p className="text-sm">{customerData.account?.size}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground">
                Deal Stage
              </Label>
              <Badge variant="default" className="text-xs">
                {customerData.account?.relationship?.deal_stage}
              </Badge>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Health</Label>
              <Badge
                variant="secondary"
                className={`text-xs ${
                  customerData.account?.relationship?.account_health === "Good"
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    : customerData.account?.relationship?.account_health ===
                        "Fair"
                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                      : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                }`}
              >
                {customerData.account?.relationship?.account_health}
              </Badge>
            </div>
          </div>

          {/* Key Contact */}
          <div>
            <Label className="text-xs text-muted-foreground">
              Main Contact
            </Label>
            <p className="text-sm">
              {customerData.account?.main_contact?.name} -{" "}
              {customerData.account?.main_contact?.title}
            </p>
            <p className="text-xs text-muted-foreground">
              {customerData.account?.main_contact?.email}
            </p>
          </div>

          {/* Active Users Metric */}
          {customerData.recent_activity?.product_usage && (
            <div>
              <Label className="text-xs text-muted-foreground">
                Active Users
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">
                  {customerData.recent_activity.product_usage.active_users}
                </span>
                <Badge variant="outline" className="text-xs">
                  {
                    customerData.recent_activity.product_usage
                      .active_users_change
                  }
                </Badge>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
