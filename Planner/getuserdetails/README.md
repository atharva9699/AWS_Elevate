-----

## Purpose of this Lambda function

This Lambda function, typically named **get\_user\_details**, is used by the QnA Bedrock Agent to **retrieve the complete profile details for a specified user** from the backend data store.

It performs a direct lookup against the primary key of the `user_profile` table and returns all available user attributes, such as email, name, certifications achieved, and current progress.

-----

## Key Responsibilities

1️) Parse and Validate Input

The function extracts the following **required parameter**:

  * **username** (String)

The function supports parameters supplied in both `event['parameters']` (Bedrock Agent standard) and `event['requestBody']` (fallback). If the `username` is provided, it is converted to lowercase for case-insensitive lookup.

2️) Read from user\_profile Table

  * **Initialize DynamoDB:** Sets up the AWS DynamoDB client.
  * **Lookup:** Performs a `GetItem` operation on the **user\_profile** table, using the lowercase `username` as the primary key.

3️) Handle Data Retrieval Outcomes

  * **User Not Found:** If the `GetItem` operation succeeds but no item is returned (i.e., the user doesn't exist), the function returns a **404 Not Found** status with a specific error message formatted for the Bedrock Agent response structure.
  * **User Found:** If the user record is found, the entire item (`user_details`) is extracted.

4️) Return Response in Bedrock Agent Format

On success, the function returns the retrieved `user_details` record with HTTP 200:

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": ...,
    "apiPath": ...,
    "httpMethod": "GET",
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": {
          // Full user_profile record (dict)
        }
      }
    }
  }
}
```

-----

## Error Handling

The function handles failure scenarios with proper HTTP status codes:

| Scenario | Status | Message (or JSON Error Body) |
| :--- | :--- | :--- |
| **Missing username** | **400** | JSON body: `{'error': 'username is required'}` |
| **User not found** | **404** | "User with username 'X' not found" |
| **DynamoDB ClientError** (e.g., table access issues, throttling) | **500** | "DynamoDB error: ..." |
| **Any other exception** | **500** | "Unhandled exception: ..." |

All errors are also logged to CloudWatch.

-----

## Typical Flow Example

User asks: **"Can you remind me what certification I'm studying for?"**

  * QnA agent determines the need for user context and invokes **get\_user\_details** with `{ "username": "jane_smith" }`.
  * Lambda looks up **user\_profile** table with key: `jane_smith`.
  * Lambda retrieves the full user record, which includes fields like `email`, `recommended_cert`, and `last_login`.
  * Lambda returns the full JSON record to the agent.
  * Agent extracts the `recommended_cert` value and replies to the user (e.g., "Your current goal is the AWS Certified Solutions Architect Associate exam.").
