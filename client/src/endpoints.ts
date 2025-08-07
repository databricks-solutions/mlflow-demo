export interface Endpoint {
  displayName: string;
  // Model sering endpoint name.
  endpointName: string;
}

export const ENDPOINTS: Endpoint[] = [
  {
    displayName: "Claude Sonnet 3.7",
    endpointName: "databricks-claude-3-7-sonnet",
  },
  {
    displayName: "GPT 4o",
    endpointName: "agents-demo-gpt4o",
  },
  {
    displayName: "Llama 4 Maverick",
    endpointName: "databricks-llama-4-maverick",
  },
  {
    displayName: "Claude Sonnet 4",
    endpointName: "databricks-claude-sonnet-4",
  },
];
