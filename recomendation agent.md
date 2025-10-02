# Recommendation Agent – Implementation Doc (Single User)

---

## 🖥 Step 1: Lambda Function (Python + Bedrock + DynamoDB)

```python
import json
import boto3

# Bedrock + DynamoDB clients
brt = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserProfile")  # Single-user profile table

def lambda_handler(event, context):
    body = json.loads(event["body"])
    user_input = body.get("prompt", "Suggest an AWS certification for a beginner.")

    # Fetch single user profile from DynamoDB
    user_profile = {}
    try:
        response = table.get_item(Key={"id": "singleUser"})
        if "Item" in response:
            user_profile = response["Item"]
    except Exception as e:
        print("DynamoDB read error:", e)

    # Combine profile with input
    combined_prompt = f"""
    User Profile: {user_profile}
    User Question: {user_input}
    Based on the profile and aspirations, recommend the most suitable AWS Certification.
    """

    # Call Bedrock model
    response = brt.invoke_model(
        modelId="amazon.titan-text-express-v1",
        body=json.dumps({
            "inputText": combined_prompt,
            "textGenerationConfig": {
                "maxTokenCount": 300,
                "temperature": 0.7
            }
        })
    )

    output = json.loads(response["body"].read())
    answer = output["results"][0]["outputText"]

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"response": answer})
    }
```

🔑 **IAM Policy needed**:

* `bedrock:InvokeModel`
* `dynamodb:GetItem`, `dynamodb:PutItem`

---

## 🗄 Step 2: DynamoDB Table (Single User)

* **Table Name**: `UserProfile`
* **Partition Key**: `id` (string)
* **Single Item**:

```json
{
  "id": "singleUser",
  "experienceLevel": "Beginner",
  "currentRole": "Business Analyst",
  "careerGoals": "Work with GenAI solutions",
  "previousCerts": []
}
```

This allows the agent to **remember context for the single user** and recommend certs accordingly.

---

## 🌐 Step 3: API Gateway

1. Create a **REST API**.
2. Add a **POST /recommend** endpoint → connect it to the Lambda.
3. Enable CORS.
4. Deploy API → copy the Invoke URL.

**Sample Request**:

```json
POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/recommend
{
  "prompt": "I want to focus more on security certifications."
}
```

**Sample Response**:

```json
{
  "response": "Based on your profile and goals, the recommended AWS Certification is AWS Certified Security – Specialty."
}
```

---

## ✅ Hackathon Demo Flow (Single User)

* Ask: **“Recommend a simple cert for a complete AWS beginner.”**
  → Agent suggests **AWS Certified Cloud Practitioner (CCP)**.

* Ask: **“I am a Business Analyst interested in GenAI.”**
  → Agent suggests **AWS Certified Data Analytics – Specialty** or GenAI-focused path.

* Ask: **“I have completed CCP and Solutions Architect Associate, now want Security.”**
  → Agent suggests **AWS Certified Security – Specialty**.

* DynamoDB keeps a **single user profile** for context throughout the session.

---

⚡ **Result**:
End-to-end **Recommendation Agent** for a single user:

* Lambda + Bedrock for recommendation logic
* Single DynamoDB item for profile
* API Gateway for interaction
