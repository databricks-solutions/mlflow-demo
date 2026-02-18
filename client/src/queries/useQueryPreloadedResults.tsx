import { useQuery } from "react-query";

export function useQueryPreloadedResults() {
  return useQuery({
    queryKey: ["preloaded-results"],
    queryFn: async () => {
      const response = await fetch("/api/preloaded-results");
      if (!response.ok) {
        throw new Error("Failed to fetch preloaded results");
      }
      return response.json();
    },
  });
}
