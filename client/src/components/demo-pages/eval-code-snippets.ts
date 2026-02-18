/** Constants and code snippet strings for the evaluation demo page */

export const SAMPLE_EVAL_QUESTIONS = [
  "How does the 2024 Kansas City Chiefs offense approach third-and-long situations?",
  "What are the most common passing concepts used by the 2023 San Francisco 49ers in the red zone?",
  "What tendencies does the 2024 Dallas Cowboys offense show on first down?",
  "How does the 2024 Miami Dolphins offense attack Cover 2 defenses?",
  "Which running plays are most effective for the 2024 Chicago Bears against a blitz?",
];

export const introContent = `
# Why Evaluate? Coaches Don't Trust Black Boxes

When a defensive coordinator asks "What do the Cowboys do on 3rd and 6?", the DC Assistant queries Unity Catalog tools, synthesizes play-by-play data, and generates tactical recommendations. But **how do you know those recommendations are actually good?** A wrong tendency read or hallucinated statistic could lead to a bad game plan.

Evaluation is how you systematically measure agent quality so you can improve it. MLflow provides three types of scorers to build a comprehensive evaluation suite:

### 1. Built-in Judges
Research-backed judges from Databricks that evaluate common quality dimensions out of the box. No configuration needed.
- Example: **ToolCallEfficiency** checks whether the DC Assistant called the right Unity Catalog functions without redundant calls

### 2. Custom Guidelines Judges
LLM judges that you configure with domain-specific rules. These are written in natural language by subject matter experts (like coaching staff) and scale their expertise to every evaluation.
- Example: **Football Language** judge checks that the response uses correct NFL terminology—formations, personnel packages, coverage schemes—the way a real coaching staff would

### 3. Code-Based Scorers
Deterministic, programmatic checks for things that don't need an LLM to evaluate. These are fast, cheap, and always consistent.
- Example: **ResponseLengthChecker** asserts the response is under 10 sentences to keep answers concise

The same scorers can be used to both **evaluate quality in development** and **monitor quality in production**.
`;

export const INITIAL_GUIDELINES = [
  {
    id: "football-language",
    name: "Football Language",
    content: "The response uses appropriate NFL terminology and coaching language based on these rules:\n" +
      "- Uses correct football terminology (formations, personnel packages, schemes)\n" +
      "- References specific plays, situations, and tendencies using standard NFL nomenclature\n" +
      '- Avoids overly technical jargon that wouldn\'t be used by coaching staff\n' +
      '- Uses down-and-distance notation correctly (e.g., "3rd and 6", "2nd and long")\n' +
      "- Personnel packages referenced correctly (11 = 1 RB, 1 TE, 3 WR; 12 = 1 RB, 2 TE, 2 WR, etc.)\n" +
      "- Formation names align with standard NFL terminology (I-formation, shotgun, pistol, etc.)\n" +
      "- Coverage and blitz schemes use standard coaching terminology (Cover 2, Cover 3, A-gap pressure, etc.)\n" +
      "- AUTOMATIC FAIL if incorrect terminology is used or if language suggests lack of football knowledge",
  },
  {
    id: "football-analysis",
    name: "Football Analysis",
    content: "The response provides actionable defensive coordinator recommendations based on these rules:\n" +
      "- Analysis must be grounded in the actual play-by-play data queried from Unity Catalog tools\n" +
      "- Tendencies must include specific percentages or frequency metrics when available\n" +
      "- Recommendations must be strategically sound for game planning (not generic advice)\n" +
      "- Must address the specific situation asked about (down-and-distance, red zone, personnel, etc.)\n" +
      "- Include key matchups or player-specific insights when relevant to the query\n" +
      "- Provide clear defensive adjustments or counter-strategies\n" +
      "- Must avoid hallucinating data not present in the tool call results\n" +
      "- AUTOMATIC FAIL if recommendations are generic, not data-driven, or strategically unsound",
  },
];

export const builtinJudgesCode = `import mlflow
import mlflow.genai
from mlflow.genai.scorers import (
    RelevanceToQuery,
    Safety,
    ToolCallCorrectness,
    ToolCallEfficiency,
)
from datetime import datetime

# Create instances of applicable built-in judges
builtin_scorers = [
    RelevanceToQuery(),
    Safety(),
    ToolCallCorrectness(),
    ToolCallEfficiency(),
]

print("\\u2705 Created built-in scorers for DC Assistant:")
for scorer in builtin_scorers:
    print(f"   - {scorer.__class__.__name__}")

# Load recent production traces for evaluation
traces = mlflow.search_traces(
    max_results=5,
    filter_string='attributes.status = "OK" and tags.sample_data = "yes"',
    order_by=['attributes.timestamp_ms DESC']
)

# Define prediction function for evaluation
def predict_fn(question_data: dict):
    """Generate DC analysis for evaluation - uses current production prompt"""
    from databricks.agents import ResponsesAgent

    # Agent is already deployed as Model Serving endpoint
    # This would call the endpoint to generate analysis
    question = question_data.get("question")
    response = agent.predict({
        "input": [{"role": "user", "content": question}]
    })
    return response

# Run the evaluation
with mlflow.start_run(
    run_name=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_dc_quality_metrics'
) as run:
    results = mlflow.genai.evaluate(
        data=traces,
        predict_fn=predict_fn,
        scorers=builtin_scorers,
    )
    run_id = run.info.run_id

print(f"\\u2705 Evaluation completed! Run ID: {run_id}")`;

export const customJudgesCode = `import mlflow
from mlflow.genai.scorers import Guidelines

# Define custom guidelines for DC Assistant quality
custom_guidelines = [
    {
        "name": "Football Language",
        "guideline": """The response uses appropriate NFL terminology and coaching language based on these rules:
- Uses correct football terminology (formations, personnel packages, schemes)
- References specific plays, situations, and tendencies using standard NFL nomenclature
- Avoids overly technical jargon that wouldn't be used by coaching staff
- Uses down-and-distance notation correctly (e.g., "3rd and 6", "2nd and long")
- Personnel packages referenced correctly (11 = 1 RB, 1 TE, 3 WR; 12 = 1 RB, 2 TE, 2 WR, etc.)
- Formation names align with standard NFL terminology (I-formation, shotgun, pistol, etc.)
- Coverage and blitz schemes use standard coaching terminology (Cover 2, Cover 3, A-gap pressure, etc.)
- AUTOMATIC FAIL if incorrect terminology is used or if language suggests lack of football knowledge"""
    },
    {
        "name": "Football Analysis",
        "guideline": """The response provides actionable defensive coordinator recommendations based on these rules:
- Analysis must be grounded in the actual play-by-play data queried from Unity Catalog tools
- Tendencies must include specific percentages or frequency metrics when available
- Recommendations must be strategically sound for game planning (not generic advice)
- Must address the specific situation asked about (down-and-distance, red zone, personnel, etc.)
- Include key matchups or player-specific insights when relevant to the query
- Provide clear defensive adjustments or counter-strategies
- Must avoid hallucinating data not present in the tool call results
- AUTOMATIC FAIL if recommendations are generic, not data-driven, or strategically unsound"""
    }
]

# Create Guidelines scorers
custom_scorers = [
    Guidelines(name=g["name"], guidelines=g["guideline"])
    for g in custom_guidelines
]

# Combine all scorers
all_scorers = builtin_scorers + custom_scorers

# Run evaluation with combined scorers
results = mlflow.genai.evaluate(
    data=traces,
    predict_fn=predict_fn,
    scorers=all_scorers,
)
`;

export const customCodeMetricsCode = `import mlflow
from mlflow.entities import Feedback, Trace
from mlflow.genai.scorers import scorer

@scorer
def response_length_checker(trace: Trace) -> Feedback:
    """Assert the response is under 10 sentences"""
    response = trace.data.response
    if not response:
        return Feedback(value=None, rationale="No response to evaluate")

    sentences = [s.strip() for s in response.split(".") if s.strip()]
    count = len(sentences)

    if count > 10:
        return Feedback(
            value=False,
            rationale=f"Response has {count} sentences (max 10)"
        )

    return Feedback(
        value=True,
        rationale=f"Response has {count} sentences (within limit)"
    )

# Run eval on the last 5 production traces
traces = mlflow.search_traces(max_results=5, order_by=['attributes.timestamp_ms DESC'])

mlflow.genai.evaluate(
    data=traces,
    predict_fn=predict_fn,
    scorers=[response_length_checker],
)
`;
