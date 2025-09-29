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
