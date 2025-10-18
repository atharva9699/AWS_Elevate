## Lambda Function: Update Recommended Certification

### Purpose

This AWS Lambda function updates the recommended_cert field for a specific user in the `user_profile` DynamoDB table. This is done so that the other collaborator agents are also aware about the specific cert recommended to the user. It is designed to be used by AWS Bedrock Agents or API integrations to store the recommended AWS certification for a user.

### Key Responsibilities

- Parse input event to extract username and recommended_cert

- Validate required parameters

- Update the DynamoDB record for the user

- Return a Bedrock-compatible response on success

- Properly handle errors (missing params, DynamoDB errors, or unexpected exceptions)

---------------
### Input Structure

The function supports two ways of receiving parameters:

1. event["parameters"] (Preferred by Bedrock Agents)

```json
"parameters": [
  {"name": "username", "value": "john_doe"},
  {"name": "recommended_cert", "value": "AWS Solutions Architect"}
]
```

2. event["requestBody"] (Fallback – optional)

Used when the request is structured like an OpenAPI call.

---------------

### Required Parameters :

|  **Parameter**                                             |  **Type**                            |   **Deescription**          
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |-------------------------------------------------------|
| **username** | “string" | Unique identifier for the user
| **recommended_cert**| “string" | 	AWS certification to be set

If either parameter is missing, the function returns a 400 Bad Request response.

-------------

### DynamoDB Usage

- Table Name: user_profile

- Primary Key: username

- Field Updated: recommended_cert
----------------

### Update operation:

- UpdateExpression="SET recommended_cert = :recommended_cert"

- Success Response (Bedrock Format)

On success, the function returns a Bedrock agent–compatible response with:

HTTP 200 status

-------------
### Confirmation message

Updated attributes

Example:

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": "update_cert",
    "httpMethod": "POST",
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": {
          "message": "Recommended certification updated successfully for user: john_doe",
          "username": "john_doe",
          "recommended_cert": "AWS Solutions Architect",
          "updatedAttributes": {
            "recommended_cert": "AWS Solutions Architect"
          }
        }
      }
    }
  }
}
```

---------
### Summary

This Lambda function provides a reliable way to:
- Update user certification preferences
- Support multiple input formats
- Integrate seamlessly with Bedrock Agents
- Return structured responses
- Handle errors safely

It is a critical building block in a certification recommendation and preparation system.
