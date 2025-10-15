Here is the information for the **Recommendation Agent** in a Markdown file format.

-----

# Recommendation Agent

### Purpose of this Agent:

The purpose of the Recommendation Agent is to suggest the most relevant **AWS certifications** to users based on their experience, role, and career goals.

### Behavior:

  - When a user requests a certification recommendation, the agent gathers essential attributes such as their AWS experience, current role, and career goals.
  - It checks if it has enough information to provide a solid recommendation, prompting for essential attributes if they are missing.
  - The agent draws on user input and information from a user profile to provide a personalized suggestion.
  - After processing the information, it calls a Lambda function to generate a recommendation and provide a rationale to support it.
  - The agent can also suggest a specific AWS domain if the user is interested.

This process ensures that the recommendation is accurate, personalized, and relevant to the user's specific needs and aspirations.

-----

### Architecture Diagram:

-----

### User Interaction with Planner Agent:

User gives the following prompt:

**User**: "Hi, I'm John, I'm a data engineer, I have cleared the CCP exam, and I'm interested in exploring data science and analysis. Which AWS cert would you recommend?"

The **Planner Agent** identifies the user's request as a recommendation query. It then routes the request to the **Recommendation Agent**. The Recommendation Agent uses its tools and databases to process the user's information and provides a tailored recommendation.

**Recommendation Agent's Response:**

"Since you are a data engineer with a CCP cert and you want to focus on data science and analysis, I'll recommend the **AWS Certified Data Analytics – Specialty** certification. This cert is designed for professionals who perform complex data analysis and covers key AWS data services like Kinesis, Athena, and Redshift. Would you like to know more about this cert?"

-----

### AWS Services:

#### Use of AWS Bedrock Agents

This project uses **AWS Bedrock Agents** to create the Recommendation Agent, providing a scalable and modular solution.

  - **Seamless Agent Development**: Bedrock Agents offer a managed framework for defining agent logic, integrating with services like **Lambda** and **DynamoDB**, and managing conversation flows without complex manual orchestration.
  - **Powered by a Foundation Model**: The agent uses a powerful large language model (LLM) for natural language understanding and reasoning, allowing for:
      - High-quality recommendations.
      - Context-aware responses.
      - Understanding of user's roles and goals.
  - **Memory for Summarization**: Memory is used to:
      - Store key user profile details (e.g., previous certifications, experience level).
      - Maintain contextual continuity across conversations.
      - Personalize recommendations based on a user's history and progress.
  - **Collaboration via Agent Alias**: An alias is created to enable collaboration with the **Planner Agent**. This allows for:
      - **Agent-to-agent communication**.
      - The Planner Agent to delegate the task of providing a recommendation to the appropriate collaborator agent.
      - Clean version and environment management.
