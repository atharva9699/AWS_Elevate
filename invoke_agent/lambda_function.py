import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Replace these with your actual values
AGENT_ID = 'MFHMV9L4SS'
AGENT_ALIAS_ID = 'COVZOLG2LV'

def lambda_handler(event, context):
    """
    Lambda function to interact with AWS Bedrock Agent
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        print("INSIDE INVOKE AGENT LAMBDA FUNCTION")
        print("Full event:", json.dumps(event, indent=2))
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        user_message = body.get('message', '')
        session_id = body.get('sessionId', f'session-{context.aws_request_id}') 

        username = "charles"
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            enableTrace=True,
            streamingConfigurations={
                'streamFinalResponse': False
            },
            inputText=user_message
        )

        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        messages_table = dynamodb.Table("messages")
        
        # Collect the response from the stream
        agent_response = ""
        event_stream = response["completion"]
        chunk_count = 0

        try:
            for event in event_stream:
                chunk_count += 1
                print(f"Event {chunk_count} received:", json.dumps(event, default=str))

                # Handle chunk events - the main response content
                if "chunk" in event:
                    chunk = event["chunk"]
                    
                    # Text chunks with bytes
                    if "bytes" in chunk:
                        decoded_text = chunk["bytes"].decode("utf-8")
                        print(f"Chunk {chunk_count} text: {decoded_text}")
                        agent_response += decoded_text
                        log_message(
                            messages_table,
                            username,
                            "FINAL_RESPONSE",
                            f"{agent_response}"
                        )
                    
                    # Attribution can also contain text
                    if "attribution" in chunk:
                        print("Attribution:", chunk["attribution"])

                # Handle returnControl for action group responses
                elif "returnControl" in event:
                    return_control = event["returnControl"]
                    if "invocationInputs" in return_control:
                        for inv_input in return_control["invocationInputs"]:
                            if "functionInvocationInput" in inv_input:
                                func_input = inv_input["functionInvocationInput"]
                                print("Function invocation:", func_input)
                
                # Handle trace events for debugging
                elif "trace" in event:
                    trace = event["trace"]
                    print("Trace event type:", list(trace.keys()))
                    
                    # Handle nested trace structure (trace → trace → orchestrationTrace)
                    inner_trace = trace.get("trace", {})
                    
                    # Handle rationale events from orchestration trace
                    if "orchestrationTrace" in inner_trace:
                        orchestration_trace = inner_trace["orchestrationTrace"]
                        if "rationale" in orchestration_trace:
                            rationale = orchestration_trace["rationale"]
                            rationale_text = rationale.get("text", "")
                            trace_id = rationale.get("traceId", "")
                            
                            print(f"Rationale event detected (TraceId: {trace_id})")
                            print(f"Rationale text: {rationale_text}")
                            
                            # Log the rationale event
                            log_message(
                                messages_table,
                                username,
                                "RATIONALE",
                                "RATIONALE: (1) " + rationale_text,
                                show_to_user=False,
                                agent="Orchestration"
                            )
                        
                        # Handle agent collaborator invocations within orchestration trace
                        if "invocationInput" in orchestration_trace:
                            invocation_input = orchestration_trace["invocationInput"]
                            if "agentCollaboratorInvocationInput" in invocation_input:
                                agent_collab_input = invocation_input["agentCollaboratorInvocationInput"]
                                agent_name = agent_collab_input.get("agentCollaboratorName", "Unknown")
                                
                                print(f"Agent collaborator invoked: {agent_name}")
                                
                                # Log the agent collaborator event
                                log_message(
                                    messages_table,
                                    username,
                                    "AGENT_COLLABORATOR",
                                    f"AGENT_COLLABORATOR: {agent_name} Agent invoked",
                                    show_to_user=False,
                                    agent=agent_name
                                )
                    
                    # Handle routing classifier trace for agent collaborator invocations
                    elif "routingClassifierTrace" in inner_trace:
                        routing_trace = inner_trace["routingClassifierTrace"]
                        if "invocationInput" in routing_trace:
                            invocation_input = routing_trace["invocationInput"]
                            if "agentCollaboratorInvocationInput" in invocation_input:
                                agent_collab_input = invocation_input["agentCollaboratorInvocationInput"]
                                agent_name = agent_collab_input.get("agentCollaboratorName", "Unknown")
                                
                                print(f"Agent collaborator invoked: {agent_name}")
                                
                                # Log the agent collaborator event
                                log_message(
                                    messages_table,
                                    username,
                                    "AGENT_COLLABORATOR",
                                    f"AGENT_COLLABORATOR: {agent_name} Agent invoked",
                                    show_to_user=False,
                                    agent=agent_name
                                )
                    
        except Exception as stream_error:
            print(f"Error reading stream: {str(stream_error)}")
            import traceback
            print(f"Stream traceback: {traceback.format_exc()}")
        
        print(f"Total chunks received: {chunk_count}")
        print(f"Final agent response length: {len(agent_response)}")
        print(f"Final agent response: {agent_response}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': agent_response,
                'sessionId': session_id
            })
        }
        
    except ClientError as e:
        print(f"AWS Client Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Failed to invoke Bedrock Agent',
                'details': str(e)
            })
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

def log_message(messages_table, username, message_type, message_content, show_to_user=True, agent='Overall'):
    """
    Log a message to the DynamoDB messages table with partition key (username) and sort key (created_at)
    """
    try:
        message_item = {
            'username': username,
            'created_at': datetime.utcnow().isoformat(),
            'message_type': message_type,
            'message_content': message_content,
            'timestamp_epoch': int(datetime.utcnow().timestamp()),
            'show_to_user': show_to_user,
            'agent': agent
        }
        messages_table.put_item(Item=message_item)
        print(f"Message logged: {message_type} - {message_content}")
    except Exception as e:
        print(f"Error logging message: {str(e)}")
