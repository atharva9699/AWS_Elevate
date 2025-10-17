### QnA Agent 
------------- 
## Purpose


The QnA Agent is designed to answer user questions related to AWS Certifications based on the selected certification from the user profile.
It ensures accurate, context-aware, and friendly responses using the Nova Pro model on AWS Bedrock — with integrated data retrieval from DynamoDB.
This agent acts as the knowledge expert, providing detailed insights about certification exams such as duration, cost, difficulty, topics covered, and recertification details.

------------- 
### QnA Agent workflow
<img width="1131" height="369" alt="Screenshot 2025-10-17 at 15 02 18" src="https://github.com/user-attachments/assets/49a8ddce-2d72-4fbf-b368-4c8c8ca22a12" />


## Example :

|  **User Question**                                             |  *Response **                                                                                                                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **“How much does the Solutions Architect Associate exam cost?”** | “The Solutions Architect Associate exam costs **$150**. Do you have the **50% discount voucher** from a previously cleared AWS certification?” <br> *(Fetches cost from DynamoDB, checks for cleared certs, and triggers voucher prompt.)* |
| **“What topics are covered in it?”**                             | “It covers **architecture design principles**, **service selection**, and **cost optimization** strategies. Focus on hands-on AWS experience for the best preparation.” <br> *(Retrieves topic list and summarizes using Nova Pro model.)* |

------------- 
<img width="420" height="553" alt="Screenshot 2025-10-14 at 10 12 58 PM" src="https://github.com/user-attachments/assets/a1409ebb-ccfc-40f4-a644-057da84a5b4e" />

------------- 
