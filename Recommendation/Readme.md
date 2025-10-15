```markdown
<!-- Recommendation Agent README -->
# Recommendation Agent

**Purpose:** Suggest the most relevant AWS certifications to users based on experience, role, and career goals.

**Author:** (please add your name)

**Last updated:** 2025-10-15

---

## Behavior

- When a user asks for a certification recommendation, the agent gathers essential attributes such as AWS experience, current role, and career goals.
- If required information is missing, the agent prompts the user for essential attributes.
- The agent uses user input and profile data to personalize recommendations.
- After processing, it calls a Lambda function to generate a recommendation and a supporting rationale.
- Optionally the agent can suggest a specific AWS domain when the user requests a focused path.

This flow helps ensure recommendations are accurate, personalized, and relevant to the user's goals.

---

## Example interaction (Planner -> Recommendation)

**User:** "Hi, I'm John, I'm a data engineer, I have cleared the CCP exam, and I'm interested in exploring data science and analysis. Which AWS cert would you recommend?"

The Planner Agent recognizes this as a recommendation request and forwards the relevant context to the Recommendation Agent. The Recommendation Agent responds with a tailored suggestion.

**Recommendation Agent (example):**
> Since you are a data engineer with a CCP cert and you want to focus on data science and analysis, I recommend the **AWS Certified Data Analytics – Specialty** certification. It covers AWS services such as Kinesis, Athena, and Redshift and is suited for professionals performing complex data analysis.

---

## AWS Services and Components

### Use of AWS Bedrock Agents

This project uses AWS Bedrock Agents to implement the Recommendation Agent. Key advantages:

- Managed framework for agent logic, integrations (Lambda, DynamoDB), and conversation flows.
- Uses a foundation model (LLM) for natural language understanding and reasoning.
- Memory is used to store profile details and maintain conversation context.
- An agent alias enables collaboration between Planner and Recommendation agents for delegation and environment/versioning.

---

## How to use / Test locally

1. Ensure your project has the required environment variables and AWS credentials configured (for Lambda/DynamoDB/Bedrock access).
2. Provide a sample user profile or start a conversation through the Planner Agent with the fields: name, role, experience_level, certifications, and career_goals.
3. Invoke the Recommendation Agent and verify the returned recommendation and rationale.

> Note: This README is a high-level design doc — implementation details (function names, Lambda handlers, and resource ARNs) should be added here when available.

---

## Contributing

- If you make changes to the agent logic, update this README with new usage notes.
- Add unit/integration tests for any Lambda functions used by the agent.
- Use a feature branch and open a pull request with a clear summary of changes.

```