**Purpose of this Lambda function**

This Lambda function is used by the QnA Bedrock Agent to retrieve certification details for a user.
It performs a two-step lookup:

- Read the user’s recommended certification from the user_profile table.

- Use that value to fetch the full certification details from the CertInfo table.

It then returns the result in Bedrock Agent-compatible response format.

-------

**Key Responsibilities**

1️) Parse Input from Bedrock Agent Event

The event may contain parameters in two formats:

- event['parameters'] (Bedrock Agent standard)

- event['requestBody'] (fallback option)

The function extracts the username parameter, which is required to proceed.

2️) Validate Input

If username is missing, the Lambda returns:

- HTTP 400 (Bad Request)

- JSON body explaining that the username is required.

3️) Read from user_profile Table

 Looks up: Key: { username: <username> }

- If user not found → returns 404 Not Found

- From the user profile record, it extracts:

   recommended_cert (e.g., "AWS Certified Solutions Architect")

- If this field is missing → returns 404 Not Found

4️) Lookup Certification Details

Queries the CertInfo table:

Key: CertificationName = recommended_cert

- If not found → returns 404 Not Found

- If found → retrieves full certification record (e.g. topics, duration, difficulty, exam format)

-----------

5️) Return Response in Bedrock Agent Format

On success:
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
          // full CertInfo record (dict)
        }
      }
    }
  }
}

The actionGroup, apiPath, and httpMethod values are taken dynamically from the incoming event.

  --------
