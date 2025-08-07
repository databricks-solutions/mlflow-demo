import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Users, Calendar, AlertCircle, CheckCircle2 } from "lucide-react";

interface CustomerFormProps {
  customerData: any;
  updateField: (path: string, value: any) => void;
}

export function CustomerForm({ customerData, updateField }: CustomerFormProps) {
  // Customer form is now read-only since data comes from MLflow retriever
  const industries = [
    "E-commerce",
    "Education",
    "Aerospace",
    "Transportation & Logistics",
    "Manufacturing",
    "Environmental Services",
    "Banking",
    "Energy & Utilities",
    "Legal Services",
    "Retail",
    "Technology",
    "Construction",
    "Non-profit",
    "Biotechnology",
    "Automotive",
    "Fashion",
    "Software",
    "Healthcare",
    "Pharmaceuticals",
    "Agriculture",
    "Consulting",
    "Hospitality",
    "Food & Beverage",
    "Real Estate",
    "Insurance",
    "Government",
    "Sports & Recreation",
  ];

  const companySizes = [
    "Small Business (10-50 employees)",
    "Small Business (51-100 employees)",
    "Mid-market (101-500 employees)",
    "Mid-market (501-1000 employees)",
    "Enterprise (1001-5000 employees)",
    "Enterprise (5000+ employees)",
  ];

  const dealStages = [
    "New Customer",
    "Onboarding",
    "Implementation",
    "Growth",
    "Expansion",
    "Mature",
    "At Risk",
  ];

  const healthStatuses = [
    { value: "Excellent", color: "bg-green-500" },
    { value: "Good", color: "bg-blue-500" },
    { value: "Fair", color: "bg-yellow-500" },
    { value: "Poor", color: "bg-red-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Account Details */}
      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Company Name</Label>
            <Input
              value={customerData.account.name}
              disabled
              className="mt-1"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Input
                value={customerData.account.industry}
                disabled
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="company-size">Company Size</Label>
              <Input
                value={customerData.account.size}
                disabled
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Main Contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="contact-name">Name</Label>
              <Input
                id="contact-name"
                value={customerData.account.main_contact.name}
                onChange={(e) =>
                  updateField("account.main_contact.name", e.target.value)
                }
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="contact-title">Title</Label>
              <Input
                id="contact-title"
                value={customerData.account.main_contact.title}
                onChange={(e) =>
                  updateField("account.main_contact.title", e.target.value)
                }
                className="mt-1"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="contact-email">Email</Label>
            <Input
              id="contact-email"
              type="email"
              value={customerData.account.main_contact.email}
              onChange={(e) =>
                updateField("account.main_contact.email", e.target.value)
              }
              className="mt-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* Relationship Status */}
      <Card>
        <CardHeader>
          <CardTitle>Relationship Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="customer-since">Customer Since</Label>
              <Input
                id="customer-since"
                type="date"
                value={customerData.account.relationship.customer_since}
                onChange={(e) =>
                  updateField(
                    "account.relationship.customer_since",
                    e.target.value,
                  )
                }
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="deal-stage">Deal Stage</Label>
              <Input
                value={customerData.account.relationship.deal_stage}
                disabled
                className="mt-1"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="account-health">Account Health</Label>
            <Input
              value={customerData.account.relationship.account_health}
              disabled
              className="mt-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* Sales Representative */}
      <Card>
        <CardHeader>
          <CardTitle>Sales Representative</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="rep-name">Name</Label>
              <Input
                id="rep-name"
                value={customerData.sales_rep.name}
                onChange={(e) => updateField("sales_rep.name", e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="rep-title">Title</Label>
              <Input
                id="rep-title"
                value={customerData.sales_rep.title}
                onChange={(e) => updateField("sales_rep.title", e.target.value)}
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Activity Dashboard */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Activity Summary */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Active Users
                    </p>
                    <p className="text-2xl font-bold">
                      {customerData.recent_activity.product_usage.active_users}
                    </p>
                  </div>
                  <Users className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {
                    customerData.recent_activity.product_usage
                      .active_users_change
                  }
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Last Meeting
                    </p>
                    <p className="text-lg font-semibold">
                      {customerData.recent_activity.meetings?.[0]?.date ||
                        "N/A"}
                    </p>
                  </div>
                  <Calendar className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {customerData.recent_activity.meetings?.[0]?.type || ""}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Open Tickets
                    </p>
                    <p className="text-2xl font-bold">
                      {customerData.recent_activity.support_tickets?.filter(
                        (t: any) => t.status === "Open",
                      ).length || 0}
                    </p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Meetings */}
          {customerData.recent_activity.meetings?.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Recent Meetings</h4>
              <div className="space-y-2">
                {customerData.recent_activity.meetings.map(
                  (meeting: any, index: number) => (
                    <Card key={index}>
                      <CardContent className="pt-4">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium">{meeting.type}</span>
                          <Badge variant="outline">{meeting.date}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {meeting.summary}
                        </p>
                        {meeting.action_items?.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium mb-1">
                              Action Items:
                            </p>
                            <ul className="text-xs text-muted-foreground list-disc list-inside">
                              {meeting.action_items.map(
                                (item: string, i: number) => (
                                  <li key={i}>{item}</li>
                                ),
                              )}
                            </ul>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ),
                )}
              </div>
            </div>
          )}

          {/* Product Usage */}
          <div>
            <h4 className="font-medium mb-2">Product Usage Insights</h4>
            <div className="space-y-2">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Most Used Features
                </p>
                <div className="flex flex-wrap gap-1">
                  {customerData.recent_activity.product_usage.most_used_features.map(
                    (feature: string) => (
                      <Badge
                        key={feature}
                        variant="default"
                        className="bg-green-500"
                      >
                        {feature}
                      </Badge>
                    ),
                  )}
                </div>
              </div>

              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Least Used Features
                </p>
                <div className="flex flex-wrap gap-1">
                  {customerData.recent_activity.product_usage.least_used_features.map(
                    (feature: string) => (
                      <Badge
                        key={feature}
                        variant="secondary"
                        className="bg-yellow-500"
                      >
                        {feature}
                      </Badge>
                    ),
                  )}
                </div>
              </div>

              {customerData.recent_activity.product_usage
                .potential_opportunity && (
                <Card className="bg-blue-50 dark:bg-blue-950">
                  <CardContent className="pt-4">
                    <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                      Opportunity:{" "}
                      {
                        customerData.recent_activity.product_usage
                          .potential_opportunity
                      }
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Support Tickets */}
          {customerData.recent_activity.support_tickets?.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Support Tickets</h4>
              <div className="grid grid-cols-1 gap-2">
                {customerData.recent_activity.support_tickets.map(
                  (ticket: any) => (
                    <Card
                      key={ticket.id}
                      className={
                        ticket.status === "Open"
                          ? "border-red-200"
                          : "border-green-200"
                      }
                    >
                      <CardContent className="pt-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-sm">
                                {ticket.id}
                              </span>
                              <Badge
                                variant={
                                  ticket.status === "Open"
                                    ? "destructive"
                                    : "default"
                                }
                              >
                                {ticket.status}
                              </Badge>
                              <Badge variant="outline">{ticket.priority}</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {ticket.issue}
                            </p>
                          </div>
                          {ticket.status === "Open" ? (
                            <AlertCircle className="h-5 w-5 text-red-500" />
                          ) : (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ),
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
