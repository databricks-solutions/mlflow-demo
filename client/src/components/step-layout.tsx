import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface StepLayoutProps {
  title: string;
  description: string;
  intro: React.ReactNode;
  codeSection: React.ReactNode;
  demoSection: React.ReactNode;
  children?: React.ReactNode;
}

export function StepLayout({
  title,
  description,
  intro,
  codeSection,
  demoSection,
  children,
}: StepLayoutProps) {
  return (
    <div className="w-full h-full flex flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 p-6">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="text-muted-foreground mt-2">{description}</p>
      </div>

      {/* Main Content */}
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-8">
          {/* Introduction Section */}
          <Card>
            <CardHeader>
              <CardTitle>Introduction</CardTitle>
            </CardHeader>
            <CardContent>{intro}</CardContent>
          </Card>

          {codeSection && (
            <>
              <Separator />

              {/* Code Examples Section */}
              <Card>
                <CardHeader>
                  <CardTitle>Example code</CardTitle>
                </CardHeader>
                <CardContent>{codeSection}</CardContent>
              </Card>

              <Separator />
            </>
          )}

          {/* Interactive Demo Section */}
          <Card>
            <CardHeader>
              <CardTitle>Demo</CardTitle>
            </CardHeader>
            <CardContent>{demoSection}</CardContent>
          </Card>

          {/* Additional Content */}
          {children && (
            <>
              <Separator />
              {children}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
