***

## Purpose of this Lambda function

This Lambda function, typically named **invoke\_agent**, serves as the **API gateway interface** for the user-facing application to interact with the **AWS Bedrock Agent**.

Its primary role is to:
1.  Receive a user message (prompt) via an API call (HTTP POST).
2.  Invoke the configured **Bedrock Agent** with the user's message and current session context.
3.  Process the **streaming response** from the agent, extracting the final text response and logging key **trace** and **orchestration** information to DynamoDB for debugging and auditing.
4.  Return the final agent response to the client.

---

## Key Responsibilities

1️) Handle Preflight and Parse Input

* **Handle CORS Preflight:** Responds immediately with a 200 status and appropriate CORS headers if an HTTP `OPTIONS` request is received.
* **Parse Input:** Extracts two required pieces of information from the HTTP request `body`:
    * **message** (String): The user's prompt to the agent.
    * **sessionId** (String): The ongoing conversation ID, or generates a new one if missing.
* **Set Context:** Hardcodes the `username` to **"charles"** (used for logging purposes).

2️) Invoke Bedrock Agent

* Calls the `bedrock-agent-runtime.invoke_agent` API with:
    * **AGENT\_ID** and **AGENT\_ALIAS\_ID** (hardcoded configuration values).
    * The extracted **sessionId**.
    * **inputText** (The user's message).
    * `enableTrace=True` and `streamFinalResponse=False` to enable detailed logging and handle the entire event stream internally.

3️) Process and Log Response Stream

* **Collect Response:** Iterates through the streaming response (`response["completion"]`) chunk-by-chunk.
* **Handle Text Chunks:** Concatenates all `chunk["bytes"]` to build the final `agent_response` text. The full text response is logged to the DynamoDB `messages` table with the `FINAL_RESPONSE` type.
* **Handle Trace Events:** Processes **trace** events to extract crucial debugging information:
    * **Rationale:** Logs the orchestration model's **reasoning** for its actions (e.g., deciding which tool/function to call) to the `messages` table with `RATIONALE` type and `show_to_user=False`.
    * **Agent Collaborator Invocation:** Logs when the primary agent invokes a **collaborator agent** (for advanced use cases) for auditing purposes.
* **Handle Return Control:** Logs the function invocation inputs (parameters sent to the Action Group Lambda) when the agent decides to use an action group.

4️) Return Final Response

* After the stream is fully processed, the Lambda returns the collected **final agent response** text and the **sessionId** to the client with an HTTP **200** status, including the necessary CORS headers.

---

## Error Handling

The function handles API Gateway and AWS-specific errors:

| Scenario | Status | Response Body |
| :--- | :--- | :--- |
| **Missing user message** (`body['message']` is empty) | **400 (Bad Request)** | `{"error": "Message is required"}` |
| **AWS ClientError** (e.g., Bedrock Agent API failure, network issue) | **500 (Internal Server Error)** | `{"error": "Failed to invoke Bedrock Agent"}` |
| **General Exception** (e.g., JSON parsing error, DynamoDB logging issue) | **500 (Internal Server Error)** | `{"error": "Internal server error"}` |

All errors, trace events, and final responses are logged to CloudWatch and the DynamoDB `messages` table.

---

## Typical Flow Example

User sends: **"What is my recommended certification?"**

* API Gateway receives POST request and invokes **invoke\_agent**.
* Lambda extracts `message` and `sessionId`.
* Lambda calls `bedrock-agent-runtime.invoke_agent`.
* The streaming response begins:
    * Lambda receives a **Trace Event** showing the **Rationale** (e.g., "The user is asking for certification details, I will call the `load_cert_info` action group"). This is logged to DynamoDB.
    * Lambda receives a **ReturnControl Event** showing the **function invocation input** (e.g., `{"username": "charles"}`).
    * The Agent executes the action group and gets the response.
    * Lambda receives the final **Chunk Events** containing the text (e.g., "Your recommended cert is AWS Certified Solutions Architect").
    * This final text is logged to DynamoDB with the `FINAL_RESPONSE` type.
* Lambda returns **HTTP 200** with the final text response to the client.
