# Planner 

### Purpose of the planner agent.

The Planner Agent acts as the supervisor or controller of the system. It manages user sessions, establishes identity, interprets intent, and routes the request to the correct collaborator agent. Using multi-agent collaboration, it coordinates communication and integrates responses from multiple agents to ensure a unified user experience.

### Key Responsibilities

- User Identification
- If the user’s name is unknown, the Planner Agent asks for it.
- Once the name is provided (e.g., “Bruce Wayne”), it generates a username: `bruce_wayne`
### The Planner informs the user of their username only once during the first interaction.

- Example:  “Thanks, Bruce Wayne! Your username will be bruce_wayne from now on.”

### Intent Detection and Routing
Based on user input, the Planner Agent identifies the intent and delegates the task to one of its collaborator agents:
- Recommendation Agent → Suggests suitable AWS certifications.
- QnA Agent → Provides detailed information about specific certifications.
- Tutor Agent → Teaches AWS topics.
- Quiz Agent → Conducts knowledge quizzes and provides detailed result reports.
