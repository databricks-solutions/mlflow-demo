import { useQuery } from "react-query";

export function useQueryNotebookUrl(notebookName: string) {
  return useQuery({
    queryKey: ["notebook-url", notebookName],
    queryFn: async () => {
      const response = await fetch(`/api/get-notebook-url/${notebookName}`);
      if (!response.ok) {
        throw new Error("Failed to fetch notebook URL");
      }
      return response.json();
    },
    enabled: !!notebookName, // Only run query if notebookName is provided
  });
}
