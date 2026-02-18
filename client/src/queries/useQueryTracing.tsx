import { useQuery } from "react-query";

export function useQueryExperiment() {
  return useQuery({
    queryKey: ["experiment"],
    queryFn: async () => {
      const response = await fetch("/api/tracing_experiment");
      if (!response.ok) {
        throw new Error("Failed to fetch experiment");
      }
      return response.json();
    },
  });
}
