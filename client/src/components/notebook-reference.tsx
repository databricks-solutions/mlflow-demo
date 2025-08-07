import React from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, ExternalLink } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useQueryNotebookUrl } from "@/queries/useQueryNotebookUrl";

interface NotebookReferenceProps {
  notebookPath: string;
  notebookName: string;
  description?: string;
  githubUrl?: string;
}

export function NotebookReference({
  notebookPath,
  notebookName,
  description,
  githubUrl,
}: NotebookReferenceProps) {
  const { data: notebookUrlData, isLoading: isNotebookUrlLoading } =
    useQueryNotebookUrl(notebookName);

  const databricksUrl =
    notebookUrlData?.url !== "NOT FOUND" ? notebookUrlData?.url : null;

  const handleOpenNotebook = () => {
    // Prefer Databricks URL if available, then GitHub, then fallback
    if (databricksUrl) {
      window.open(databricksUrl, "_blank");
    } else if (githubUrl) {
      window.open(githubUrl, "_blank");
    } else {
      // For local development, could open VS Code or Jupyter
      console.log(`Opening notebook: ${notebookPath}`);
    }
  };

  return (
    <Card className="border-2 border-blue-200 bg-blue-50/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <BookOpen className="h-5 w-5 text-blue-600" />
          Interactive Notebook
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            For a hands-on experience with the code examples on this page, open
            the accompanying Jupyter notebook:
          </p>
          <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
            <code className="text-sm font-mono">{notebookName}</code>
            <Button
              size="sm"
              variant="outline"
              onClick={handleOpenNotebook}
              className="ml-4"
              disabled={isNotebookUrlLoading}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              {isNotebookUrlLoading
                ? "Loading..."
                : databricksUrl
                  ? "Open in Databricks"
                  : githubUrl
                    ? "Open in GitHub"
                    : "Open Notebook"}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground italic">
            The notebook contains all the code from this page plus additional
            examples and exercises you can run locally.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
