import { useQuery } from "react-query";
import { HelperService } from "../fastapi_client/services/HelperService";

export function useQueryFixedPrompt() {
  return useQuery({
    queryKey: ["fixed-prompt"],
    queryFn: async () => {
      return HelperService.getFixedPromptApiFixedPromptGet();
    },
  });
}

export function useQueryCurrentProductionPrompt() {
  return useQuery({
    queryKey: ["current-production-prompt"],
    queryFn: async () => {
      return HelperService.getCurrentProductionPromptApiCurrentProductionPromptGet();
    },
  });
}
