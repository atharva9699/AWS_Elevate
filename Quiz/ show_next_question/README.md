-----

## Purpose of this Lambda function

This Lambda function, typically named **show\_next\_question**, is used by the QnA Bedrock Agent to manage the flow of an ongoing quiz.

Its primary role is to **process the user's answer** to the current question, **update the quiz's score and state**, and then **retrieve and return the next question** in the sequence. It detects when a quiz is complete and returns the final score.

-----

## Key Responsibilities

1️) Parse and Validate Input from Bedrock Agent Event

The function attempts to extract four required parameters from the event's `event['parameters']` or `event['requestBody']` (as a fallback):

  * **quiz\_id** (String)
  * **username** (String)
  * **current\_order** (Integer/String)
  * **user\_answer** (String/Integer, e.g., 'A', 'B', 'C', 'D', or 0, 1, 2, 3)

The `username` is converted to lowercase for lookup consistency. The `current_order` and `user_answer` are validated and converted to the appropriate integer formats.

2️) Evaluate Current Question and Update Question State

  * **Read from Question Table:** Fetches the question record for the given `quiz_id` and `current_order` from the **question** table (using environment variable `QUESTION_TABLE`).
  * **Check Answer:** Compares the `user_answer` against the question's `correct_answer`.
  * **Update Question Table:** Updates the corresponding record in the **question** table, setting:
      * `user_score` (1 if correct, 0 if incorrect)
      * `answered_correctly` (Boolean)
      * `user_answer` (Integer index)

3️) Update Quiz Cumulative Score

  * **Read from Quiz Table:** Fetches the overall quiz record for the given `username` and `quiz_id` from the **quiz** table (using environment variable `QUIZ_TABLE`) to get the current total score and max score.
  * **Update Quiz Table:** Increments the quiz record's total `user_score` by the score obtained in the current question (0 or 1).

4️) Retrieve Next Question or Mark Quiz Complete

  * **Read from Question Table (Next Question):** Attempts to fetch the next sequential question using `current_order + 1`.
  * **If Found:** Prepares the response with the details of the next question (`order`, `question`, `options`), the progress, and the result of the previous question.
  * **If Not Found:** Returns a "Quiz Completed" status, including the `final_score` and `max_score`.

5️) Return Response in Bedrock Agent Format

On success (either next question or quiz completion), the result is returned with HTTP 200:

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": ...,
    "apiPath": ...,
    "httpMethod": "POST",
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": {
          "quiz_id": "...",
          "previous_question_correct": true/false,
          "correct_answer": 0-3,
          "quiz_complete": true/false,
          "current_question": { ... }, // Or final_score/max_score if complete
          "progress": { ... }
        }
      }
    }
  }
}
```

-----

## Error Handling

The function handles different failure scenarios with proper HTTP status codes, using the `create_error_response` helper function:

| Scenario | Status | Message |
| :--- | :--- | :--- |
| **Missing required input** (`quiz_id`, `username`, `current_order`, `user_answer`) | **400** | e.g., "quiz\_id is required" |
| **Invalid input format** (`current_order` not a number, `user_answer` not A-D or 0-3) | **400** | e.g., "user\_answer must be A, B, C, D or 0-3" |
| **Question not found** (for `current_order`) | **404** | "Question with order X not found for quiz Y" |
| **Quiz not found** (in quiz table) | **404** | "Quiz Y not found" |
| **DynamoDB ClientError** (on read or update) | **500** | "DynamoDB error: ..." |
| **Any other exception** | **500** | "Unhandled exception: ..." |

All errors and important steps are also logged to CloudWatch.

-----

## Typical Flow Example

User asks: **"I think the answer to question 5 is C."**

  * QnA agent invokes **show\_next\_question** with:
      * `quiz_id`: "cert\_quiz\_101"
      * `username`: "jane\_doe"
      * `current_order`: "5"
      * `user_answer`: "C"
  * Lambda retrieves Question 5 from the **question** table (e.g., correct answer is '2' / C).
  * Lambda determines the answer is **correct**.
  * Lambda updates Question 5's record (`user_score=1`) in the **question** table.
  * Lambda updates the `user_score` in the "cert\_quiz\_101" record in the **quiz** table.
  * Lambda attempts to retrieve Question 6 (`current_order + 1`).
  * Lambda returns **Question 6's details** (question text, options) and confirms **`previous_question_correct: true`** to the agent.
  * Agent displays Question 6 to the user.
