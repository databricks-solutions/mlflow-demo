import { useQuery } from "react-query";
import { DefaultService } from "../fastapi_client/services/DefaultService";

export function useQueryPreloadedResults() {
  return useQuery({
    queryKey: ["preloaded-results"],
    queryFn: async () => {
      return DefaultService.getPreloadedResultsApiPreloadedResultsGet();
    },
  });
}
