## Lambda Function: Update User Profile
### Purpose

This AWS Lambda function updates multiple fields in a user’s profile stored in the user_profile DynamoDB table.
It is designed to work with Bedrock Agents or API calls, allowing flexible updates to user data such as:

- Current/Aspiring Job Role

- Cleared Certifications

- Interest Areas

- Recommended Certification

-------

### Key Responsibilities

- Accept input from Bedrock Agent or API

- Extract parameters safely (two formats supported)

- Validate required field (username)

- Allow updates only to specific fields (security control)

- Build a dynamic DynamoDB update expression

- Update user data in DynamoDB

- Return a Bedrock-compatible structured response

- Handle errors gracefully

### Input Structure

The function supports two parameter formats:

1. From event["parameters"] (Bedrock Agent format)
"parameters": [
  {"name": "username", "value": "john_doe"},
  {"name": "currentjobrole", "value": "Cloud Engineer"},
  {"name": "interestareas", "value": "AI/ML"}
]

2. From event["requestBody"] (fallback, optional)

Used when the input comes via OpenAPI-style request.

Required Field
## Example :

|  **Field**                                             |  **Description**                                                                                                                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **username** |  Primary key of the user in DynamoDB | 

If username is missing → returns 400 Bad Request.

--------

### Allowed Updatable Fields

Only the following fields can be updated (safety measure):

- aspiringjobrole

- clearedcertifications

- currentjobrole

- interestareas

- recommended_cert

If no valid fields are found → returns 400 No valid fields to update.


----

### Error Handling

|  **Scenario**                                             |  **Description**                                                                                                                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Missing username** |  400 | "username is required" |
| **No valid update fields** |  400 | "No valid fields to update" |
| **DynamoDB error (ClientError)** |  500 | "DynamoDB error: ..." |
| **Other exceptions** |  405000 | "Unhandled exception: ..." |

All errors are logged for debugging.
