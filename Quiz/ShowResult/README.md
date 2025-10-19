***

## Purpose of this Lambda function

This Lambda function, typically named **show\_result**, is used by the QnA Bedrock Agent to provide a **comprehensive analysis and summary of a user's completed quiz**.

It retrieves all quiz data, calculates the final score, and leverages **Amazon Bedrock** (specifically, the `bedrock-runtime` client) to generate **detailed explanations for incorrect answers** and **identify personalized knowledge gaps** with study recommendations.

---

## Key Responsibilities

1️) Parse and Validate Input

The function extracts two **required parameters** from the event:
* **quiz\_id** (String)
* **username** (String)

The `username` is converted to lowercase for lookup consistency.

2️) Fetch Quiz Data and Question History

* **Read from Quiz Table:** Fetches the overall quiz metadata (including `username`, `recommended_cert`, `topic`, and `max_score`) from the **quiz** table using `username` and `quiz_id`.
* **Query Question Table:** Fetches **all question records** associated with the `quiz_id` from the **question** table.
* **Calculate Score:** Iterates through all questions to calculate the `user_score` (sum of `answered_correctly` flags) and prepares a detailed `question_summary`.

3️) Generate Detailed Explanations (Bedrock Integration)

* Calls the `generate_explanations_with_bedrock` helper function.
* Sends the list of all questions and the user's answers to a **Bedrock foundation model** (`us.amazon.nova-pro-v1:0`).
* **The model is instructed** to act as an expert certification instructor and return a JSON array of detailed explanations, focusing on:
    * Why the correct answer is right.
    * Why the user's answer was incorrect.
    * Key concepts to study.

4️) Identify Knowledge Gaps and Recommendations (Bedrock Integration)

* Calls the `identify_knowledge_gaps` helper function, passing only the **incorrectly answered questions**.
* **The model is instructed** to act as an AWS certification advisor and return a JSON object detailing:
    * An overall performance assessment.
    * Specific knowledge gaps with severity.
    * Recommended learning topics and study priorities.

5️) Prepare and Return Final Response

* Calculates the final percentage score.
* Generates a brief **performance summary** based on the percentage score (e.g., "Excellent," "Good performance").
* Formats the total score, percentage, detailed explanations, and knowledge gaps into a single response body.
* Returns the result in the standard **Bedrock Agent-compatible response format** with HTTP 200, ensuring `Decimal` types from DynamoDB are handled correctly using `DecimalEncoder`.

---

## Error Handling

The function handles different failure scenarios with proper HTTP status codes:

| Scenario | Status | Message |
| :--- | :--- | :--- |
| **Missing required input** (`quiz_id`, `username`) | **400** | e.g., "quiz\_id is required" |
| **Quiz not found** (in quiz table) | **404** | "Quiz 'X' not found" |
| **No questions found** (for the quiz ID) | **404** | "No questions found for quiz 'X'" |
| **DynamoDB ClientError** (on read or query) | **500** | "DynamoDB error: ..." |
| **Bedrock/JSON Error** (e.g., Bedrock API failure, or invalid JSON response from the model) | **500** | Handled internally by helper functions; a generic error might propagate if Bedrock is unreachable. |
| **Any other exception** | **500** | "Unhandled exception: ..." |

All errors are also logged to CloudWatch.

---

## Typical Flow Example

User asks: **"Show me the results and feedback for my certification quiz."**

* QnA agent invokes **show\_result** with `{ "username": "jane_doe", "quiz_id": "cert_quiz_101" }`.
* Lambda looks up **quiz\_101** metadata and all associated **question** records.
* Lambda calculates a **final score** (e.g., 8/10).
* Lambda calls **Bedrock** to generate:
    1.  Detailed step-by-step explanations for the two incorrect answers.
    2.  A knowledge gap assessment (e.g., "Weakness in VPC Endpoints") with study recommendations.
* Lambda compiles the score, summary, explanations, and gaps.
* Lambda returns the complete analysis to the agent in Bedrock format.
* Agent displays the full result, score, and personalized study plan to the user.
