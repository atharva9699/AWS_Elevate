
## Architecture diagram

<img width="831" height="587" alt="Screenshot 2025-10-20 at 15 10 51" src="https://github.com/user-attachments/assets/1a5a4cb7-0454-430e-968a-cde485b6668b" />





## Planner Agent 

Planner agent takes username and assists the user by routing the request to desired agents like Recommendation, QnA, Tutor and Quiz.
It's a conversational framework built using AWS Bedrock agents. The system assists users in exploring, learning, and testing their AWS certification knowledge through a Planner agent that orchestrates collaboration among specialized agents: Recommendation, QnA, Tutor, and Quiz.

## Responsibilities of Planner:

- Identify the user and set a consistent username
- Understand what the user wants (intent detection)
- Route the request to the correct specialist agent
- Guide the user through the certification process (recommendation → learning → quiz → mastery)
- User Identification & Username Handling
- If the user has not provided their name, the system asks for it.

Once the user shares their name, the system:
- Converts it to concatenated lowercase with underscore
  Example: “Bruce Wayne” → bruce_wayne
- Treats this as their username for all future requests
- Informs the user of their username ONLY on the first interaction

On future interactions, the system uses the username silently.
Overview

----------------------

## Core Agent: Planner Agent (Supervisor)

Purpose

The Planner Agent acts as the supervisor or controller of the system. It manages user sessions, establishes identity, interprets intent, and routes the request to the correct collaborator agent. Using multi-agent        collaboration, it coordinates communication and integrates responses from multiple agents to ensure a unified user experience.

### Key Responsibilities

- User Identification
- If the user’s name is unknown, the Planner Agent asks for it.
- Once the name is provided (e.g., “Bruce Wayne”), it generates a username: `bruce_wayne`


### The Planner informs the user of their username only once during the first interaction.

- Example: “Thanks, Bruce Wayne! Your username will be bruce_wayne from now on.”

### Intent Detection and Routing
Based on user input, the Planner Agent identifies the intent and delegates the task to one of its collaborator agents:
- Recommendation Agent → Suggests suitable AWS certifications.
- QnA Agent → Provides detailed information about specific certifications.
- Tutor Agent → Teaches AWS topics at multiple levels of detail.
- Quiz Agent → Conducts knowledge quizzes and provides detailed result reports.

### Response Coordination
The Planner aggregates outputs from collaborator agents, formats them, and presents coherent responses to the user.

------

## Recommendation Agent

### Purpose

Based on the user's profile / history / aspirations recommend a relevant AWS Certification.

### Sample Requests

This agent should handle these questions **from the user**:
- Recommend a simple cert for a complete AWS beginner
- What would be a good cert for a business analyst interested in GenAI?
- I have completed CCP, Soln Arch Associate. I want to focus more on Security aspects now. What cert should I prepare for next?


### Sample Questions

This agent can ask these questions **to the user**:
- Have you cleared any AWS certs so far?
- How many years of experience do you have with AWS?
- Do you have experience with any other cloud - GCP, Azure?
- What is your current role? (Developer, Architect, Data Engineer, etc)
- What are your career goals for the next 1-2 years?
- Are you interested in any specific AWS domain? (GenAI, ML, Security, Networking, Databases, etc.)
- What is your timeline for completing the certification?

### Attributes

#### Essential Attributes
- AWS Experience Level (Beginner/Intermediate/Advanced)
- Current Role/Domain
- Career Goals/Interests

#### Optional Attributes:
- Previous AWS Certifications
- Other Cloud Experience
- Specific Technology Interests
- Timeline/Bandwidth

### Tools, DB etc

- Access to a Vector Store containing info from https://aws.amazon.com/certification/
- Other recommendation articles on which AWS cert to start with etc.
- DynamoDB - where we read from UserProfile table for all the attributes of the user which we are able to glean during our conversation.

### Overall Implementation
- The agent should check if it has enough info about the user to provide a cert recommendation.
- Some attributes are essential, some attributes are optional.
- Only prompt for the essential ones. But do not ignore the optional ones if the user mentions that.
- Rely on User Input to extract missing essential attributes.
- Call a Lambda function to provide a recommendation and rationale to support it.

### Sample Response
Since you are new to AWS and want to focus on AI, I'll recommend AWS AI Practitioner cert for you. Would you like to know more about this cert? [If user says yes, this should be handled by the Cert QnA Agent.]

---

## QnA Agent

### Purpose

Based on the user's selected cert answer Qns.

### Sample Requests

This agent should handle these questions **from the user**:
- How much does the Solutions Architect Associate exam cost?
- How much does this cert cost?
- What topics are covered in it?
- How long is the exam?
- What's the passing score?
- Do I need to recertify for it?
- What's the difference between this and the Professional cert?
- How hard is the exam?
- Can I take the exam online or do I need to go to a test center?

### Sample Questions

This agent can ask these questions **to the user**:
- Do you have the 50% discount voucher available from a previously cleared cert? [When asked about the cost]

### Tools, DB etc

- Access to a DynamoDB containing info from https://aws.amazon.com/certification/

### Overall Implementation
- The agent should check the target-cert from UserProfile table of DynamoDB.
- Retrieve relevant row(s) from the table - and use LLM to phrase a relevant answer.
- Ask the voucher question if the question is about cost and we know the user has cleared certs in the past.

### Sample Response
- The CCP exam is for a duration of 90 minutes.
- The Solution Architect Professional exam will have scenario based questions. The options will usually be very similar to each other. You will need to know the differences between various services very well to be able to select the correct answer.

---

## Knowledge Checker Agent

### Purpose

Check the user's current knowledge against the target certification syllabus to identify strengths and knowledge gaps.

### Sample Requests

This agent should handle these questions **from the user**:
- How much does the Solutions Architect Associate exam cost?
- Quiz me on EC2 and VPC
- Can you test me on all the topics?
- I think I'm ready for the exam, can you verify?
- What are my weak areas?
- Do I need to recertify for it?
- Test my knowledge on Storage.
- Give me a quick assessment of 10 Qns.


### Sample Questions

This agent can ask these questions **to the user**:
- Which certification would you like me to assess your knowledge for?
- Would you like a full assessment across all domains or focus on specific topics?
- How would you like to be assessed - through questions, scenario discussions, or both?
- Should I start with fundamental concepts or dive into advanced topics?
- How many questions would you like in this assessment session? (Suggested: 10-15)

## Attributes

#### Required Context Attributes
- Target Certification (from DynamoDB UserProfile.target_certificate)
- Assessment Scope (Full syllabus vs specific domains)
- Assessment Depth (Quick check vs comprehensive)

#### Tracked Attributes

These can be stored in DynamoDB Quiz & QuizPerformance tables - either that or in Aurora serverless.
- Domain-wise Scores
- Question Response History
- Knowledge Level per Topic
- Weak Areas Identified
- Strong Areas Identified
- Last Assessment Date
  

### Tools, DB etc

   ##### DynamoDB
- UserKnowledgeProfile: Stores assessment results, domain scores, timestamp, weak/strong areas
- UserProfile: To get target cert

##### Lambda Functions:

- GenerateRecommendation: Takes user attributes and returns top 2-3 cert recommendations with rationale
- UpdateUserProfile: Updates user attributes as conversation progresses



### Overall Implementation
- The overall idea is that the Agent will invoke Lambdas which will in turn rely on Bedrock LLMs to create a list of questions with options, correct answer, topic & rationale. The Agent will present 1 question at a time and then capture the response and provide feedback to the user after each question's attempt. And at the end of the quiz the Agent should provide an overall feedback - strong in these areas, confused in these areas, weak in these areas. You should probably learn these topics. etc.

### Sample Response
- Since you are new to AWS and want to focus on AI, I'll recommend the AWS AI Practitioner certification for you. This cert is designed for beginners and covers foundational AI/ML concepts along with AWS AI services like Bedrock, SageMaker, and Rekognition. It's a great starting point before moving to the ML Specialty cert. Would you like to know more about this cert?

--- 

##  Teacher/Private Tutor Agent

### Purpose
- This agent will provide personalized, focused lessons on specific topics, domains, or weak areas identified during knowledge assessment. Offer interactive learning with explanations, examples, hands-on scenarios, and practice questions.

### Sample Requests

This agent should handle these questions **from the user**:
- Teach me about IAM policies
- I don't understand the difference between Security Groups and NACLs
- I'm confused about S3 storage classes
- Walk me through a multi-region architecture design
- What's the best way to secure an RDS database?

### Sample Questions

This agent can ask these questions **to the user**:

- Which topic would you like to focus on today?
- Would you like a high-level overview first or dive straight into details?
- Would you like me to explain using a real-world use case?
- Does this make sense so far, or should I clarify anything?
- Would you like to try a practice question on this topic?


## Attributes

#### Required Context

- Target Certification
- Specific Topic/Domain to Cover
- User's Role/Experience Level
- Learning Style Preference

#### Session Attributes

- Topics Covered in Session
- Practice Questions Attempted
- Misconceptions Corrected
- Session Duration
- Follow-up Topics Identified


### Tools, DB etc

##### DynamoDB Tables:

- CertificationSyllabus: To understand topic context within exam syllabus
- UserKnowledgeProfile: To check weak areas and previous assessment results
- LearningMaterials: Contains curated explanations, diagrams, use cases for each topic
- TutoringHistory: Tracks all tutoring sessions, topics covered, user comprehension signals
- UserProfile: For personalization (role, experience level)

#### S3 Vector is available

#### Lambda Functions:

- GenerateLesson: Creates structured lesson plan for a topic
- FetchExamples: Retrieves relevant real-world examples and scenarios
- GeneratePracticeQuestion: Creates contextual practice questions
- AssessComprehension: Analyzes user responses to gauge understanding
- RecommendNextTopic: Suggests related topics to study next

### Overall Implementation

#### Phase 1: Topic Selection & Contextualization

- Check if user arrived from Knowledge Checker Agent with specific weak topics
- If not, ask user what they want to learn
- Retrieve topic details from CertificationSyllabus
- Check UserKnowledgeProfile for any previous struggles with this topic
- Check TutoringHistory to avoid repeating the same explanations
- Personalize approach based on UserProfile.role and experience level

#### Phase 2: Lesson Planning

- Invoke GenerateLesson Lambda with:

   - Topic name and syllabus context
   - User's role and experience level
   - Learning style preference (if known)
   - Related topics from previous sessions


- Create structured lesson outline:

  - What: Definition and core concepts
  - Why: Use cases and importance for exam
  - How: Configuration, implementation details
  - When: Decision criteria for using this service/feature
  - Gotchas: Common mistakes and exam traps



#### Phase 3: Interactive Teaching

- Explain Core Concepts:

  - Start with simple explanation
  - Build up to complex details
  - Use analogies related to user's domain when possible


- Provide Examples:

  - Invoke FetchExamples to get real-world scenarios
  - Show architecture diagrams from S3 (return as image references)
  - Walk through step-by-step implementations
  - Compare with alternative approaches


##### Interactive Elements:

  - Ask comprehension check questions
  - Present "What would you do?" scenarios
  - Encourage user to ask questions
  - Correct misconceptions immediately with detailed explanations


#### Relate to Exam:

  - Highlight how this topic appears in exam questions
  - Share common question patterns
  - Explain answer elimination strategies for this topic

-------

<img width="1574" height="1252" alt="image" src="https://github.com/user-attachments/assets/1c9646be-38cf-4dbe-8337-21c1979b2582" />

