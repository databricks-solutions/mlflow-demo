import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";

interface CodeSnippetProps {
  code: string;
  language?: string;
  title?: string;
  filename?: string;
  showCopy?: boolean;
}

export function CodeSnippet({
  code,
  language = "python",
  title,
  filename,
  showCopy = false,
}: CodeSnippetProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy code:", error);
    }
  };

  return (
    <Card className="w-full">
      {(title || filename || showCopy) && (
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            {title && <CardTitle className="text-lg">{title}</CardTitle>}
            {filename && (
              <p className="text-sm text-muted-foreground font-mono">
                {filename}
              </p>
            )}
          </div>
          {showCopy && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={copied}
              className="h-8"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
          )}
        </CardHeader>
      )}
      <CardContent className="p-0">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          className="!m-0 !bg-gray-900"
          customStyle={{
            margin: 0,
            borderRadius: title || filename ? "0 0 0.5rem 0.5rem" : "0.5rem",
          }}
          wrapLines={true}
          wrapLongLines={true}
        >
          {code}
        </SyntaxHighlighter>
      </CardContent>
    </Card>
  );
}
