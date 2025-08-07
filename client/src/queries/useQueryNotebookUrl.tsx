import { useQuery } from "react-query";
import { HelperService } from "../fastapi_client/services/HelperService";

export function useQueryNotebookUrl(notebookName: string) {
  return useQuery({
    queryKey: ["notebook-url", notebookName],
    queryFn: async () => {
      return HelperService.getNotebookUrlRouteApiGetNotebookUrlNameGet(
        notebookName,
      );
    },
    enabled: !!notebookName, // Only run query if notebookName is provided
  });
}
