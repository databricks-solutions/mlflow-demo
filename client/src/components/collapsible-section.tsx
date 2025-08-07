import React from "react";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  variant?: "simple" | "advanced";
  docsUrl?: string;
}

export function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  variant = "simple",
  docsUrl,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  const variantStyles = {
    simple: "bg-gray-100 text-gray-900 border-gray-300",
    advanced: "bg-gray-50 text-gray-600 border-gray-200",
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="outline"
          className={`w-full justify-between ${variantStyles[variant]} hover:bg-opacity-80`}
        >
          <div className="flex items-center gap-3">
            <span className="font-medium">{title}</span>
            {docsUrl && (
              <a
                href={docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-3 w-3" />
                View Docs
              </a>
            )}
          </div>
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-4 p-4 border rounded-md border-muted bg-muted/30">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}
