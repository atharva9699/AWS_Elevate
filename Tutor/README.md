*Tutor*
--------------
**Purpose of this Agent:**

The agent is designed to assist users in preparing for AWS certification exams by delivering structured and relevant teaching content.

***Behavior:***
 - When the user requests a specific domain or topic, the agent provides instructional content at the depth required for the corresponding AWS certification level.
 - If the user does not specify a domain, the agent selects a topic from the AWS certification syllabus and generates teaching content automatically.
 - After each session or lesson, the agent prompts the user to continue learning, enabling an iterative and personalized learning experience.

This approach ensures comprehensive syllabus coverage, user-driven flexibility, and effective exam preparation.

------------- 
**Architecture Diagram:** 

<img width="798" height="277" alt="Screenshot 2025-10-20 at 14 28 46" src="https://github.com/user-attachments/assets/ac77ab7f-ae7e-462d-9587-df3b060b9fb1" />


***User Interaction with Planner agent:***

User gives following prompt: 

User: hi I'm John, I'm a data engineer, I have cleared CCP exam, I'm interest to explore about data science and analysis, which aws cert would you recommend?

<img width="1164" height="439" alt="Screenshot 2025-10-14 at 17 29 46" src="https://github.com/user-attachments/assets/69d6c316-f1bb-4a7c-a12d-5c57156ee94a" />



- User asks through the chat interface to describe which topics are covered in the recommended cert?
Then Planner agent analysis the reusers request and routes the request to the Tutor agent, and with the help of LLM the Tutor agent is able to reply to the user’s question.



<img width="1164" height="486" alt="Screenshot 2025-10-14 at 17 32 20" src="https://github.com/user-attachments/assets/b47f2cca-7066-4e4b-8579-8f9c7520e141" />

-----------------

**AWS services:**

Use of AWS Bedrock Agents. 

This project utilizes AWS Bedrock Agents to develop the learning assistant in a scalable, managed, and modular way.

 - Seamless Agent Development: Bedrock Agents offer a framework to define agent logic, integrate with AWS services (e.g., Lambda, DynamoDB), and manage conversation flows without    building complex orchestration manually.
 - Powered by Nova Pro Model: The agent uses the Nova Pro model for natural language understanding and reasoning, enabling:
   - High-quality explanations
   - Exam-focused guidance
   - Context-aware responses


 - Memory for Summarization
   
   Memory is used  to:
   - Store key user interaction details
   - Summarize previous sessions
   - Maintain contextual continuity
   - Personalize learning based on progress


- Collaboration via Agent Alias
  
  An alias is created to enable collaboration with the Planner Agent, allowing:
  - Agent-to-agent communication
  - Supervisor agent routes information to the appropriate collaborator agent.
  - Task delegation (e.g., planning vs. teaching)
  - Clean version and environment management






