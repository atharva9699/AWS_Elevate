### QnA Agent 
<img width="1440" height="900" alt="Screenshot 2025-10-14 at 9 30 20 PM" src="https://github.com/user-attachments/assets/a78fdd7c-7310-428c-ad3d-0b54bc512b78" />
#Purpose of this agent :
This agent is designed as the factual backbone of the system, providing quick, accurate, and administrative information regarding AWS Certification exams. Efficient retrieval and articulation of facts (cost, duration, format, policies) about specific AWS certifications.




Example :

| 💭 **User Question**                                             | 🤖 **Agent Response (Behavior)**                                                                                                                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **“How much does the Solutions Architect Associate exam cost?”** | “The Solutions Architect Associate exam costs **$150**. Do you have the **50% discount voucher** from a previously cleared AWS certification?” <br> *(Fetches cost from DynamoDB, checks for cleared certs, and triggers voucher prompt.)* |
| **“What topics are covered in it?”**                             | “It covers **architecture design principles**, **service selection**, and **cost optimization** strategies. Focus on hands-on AWS experience for the best preparation.” <br> *(Retrieves topic list and summarizes using Nova Pro model.)* |




