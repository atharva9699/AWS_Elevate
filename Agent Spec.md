# Goal 

Define the specifications for all the agents

---

## Recommendation Agent

### Purpose

Based on the user's profile / history / aspirations recommend a specific AWS Certification.

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
The overall idea is that the Agent will invoke Lambdas which will in turn rely on Bedrock LLMs to create a list of questions with options, correct answer, topic & rationale. The Agent will present 1 question at a time and then capture the response and provide feedback to the user after each question's attempt. And at the end of the quiz the Agent should provide an overall feedback - strong in these areas, confused in these areas, weak in these areas. You should probably learn these topics. etc.

### Sample Response
- Since you are new to AWS and want to focus on AI, I'll recommend the AWS AI Practitioner certification for you. This cert is designed for beginners and covers foundational AI/ML concepts along with AWS AI services like Bedrock, SageMaker, and Rekognition. It's a great starting point before moving to the ML Specialty cert. Would you like to know more about this cert?

--- 
