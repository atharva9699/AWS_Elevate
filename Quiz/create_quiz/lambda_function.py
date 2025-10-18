import json
import boto3
import os
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        print("INSIDE CREATE QUIZ LAMBDA FUNCTION")
        print("Full event:", json.dumps(event, indent=2))

        # Extract parameters from event['parameters']
        params = {}
        if 'parameters' in event:
            for param in event['parameters']:
                name = param.get('name')
                value = param.get('value')
                if name and value is not None:
                    params[name] = value

        # Fallback: try extracting from requestBody (optional)
        if not params and 'requestBody' in event:
            try:
                content = event['requestBody'].get('content', {})
                app_json = content.get('application/json', {})
                properties = app_json.get('properties', [])
                for prop in properties:
                    name = prop.get('name')
                    value = prop.get('value')
                    if name and value is not None:
                        params[name] = value
            except Exception as e:
                print(f"Error extracting from requestBody: {e}")

        # Check required parameters
        username = params.get('username')
        
        if not username:
            return create_error_response(event, 400, 'username is required')

        # lowercase username
        username = username.lower()

        # Optional parameters
        topic = params.get('topic', 'AWS General')
        num_questions = int(params.get('num_questions', 5))

        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Get table names from environment or use defaults
        user_profile_table_name = os.environ.get('USER_PROFILE_TABLE', 'user_profile')
        quiz_table_name = os.environ.get('QUIZ_TABLE', 'quiz')
        question_table_name = os.environ.get('QUESTION_TABLE', 'question')

        # Step 1: Lookup user profile to get recommended_cert
        user_profile_table = dynamodb.Table(user_profile_table_name)
        
        try:
            user_response = user_profile_table.get_item(Key={'username': username})
            if 'Item' not in user_response:
                return create_error_response(event, 404, f"User '{username}' not found")
            
            recommended_cert = user_response['Item'].get('recommended_cert', 'AWS Certified Cloud Practitioner')
        except ClientError as e:
            print(f"Error fetching user profile: {str(e)}")
            return create_error_response(event, 500, f"Error fetching user profile: {str(e)}")

        # Step 2: Generate questions using Bedrock Nova Pro
        print(f"Generating {num_questions} questions for {recommended_cert} on topic: {topic}")
        
        questions = generate_questions_with_bedrock(
            bedrock_runtime, 
            recommended_cert, 
            topic, 
            num_questions
        )
        
        if not questions:
            return create_error_response(event, 500, "Failed to generate questions")

        # Step 3: Create quiz_id and store in DynamoDB
        quiz_id = f"quiz-{uuid.uuid4()}"
        
        # Store quiz metadata
        quiz_table = dynamodb.Table(quiz_table_name)
        quiz_item = {
            'id': quiz_id,
            'username': username,
            'topic': topic,
            'recommended_cert': recommended_cert,
            'max_score': num_questions,
            'user_score': 0,
            'created_at': datetime.utcnow().isoformat()
        }
        
        quiz_table.put_item(Item=quiz_item)
        
        # Store questions
        question_table = dynamodb.Table(question_table_name)
        
        for idx, q in enumerate(questions, start=1):
            question_item = {
                'quiz_id': quiz_id,
                'order': str(idx),
                'question': q['question'],
                'options': q['options'],
                'correct_answer': q['correct_answer'],
                'user_score': 0
            }
            question_table.put_item(Item=question_item)

        # Prepare first question for response
        first_question = questions[0] if questions else None
        
        response_body = {
            "quiz_id": quiz_id,
            "total_question_count": num_questions,
            "topic": topic,
            "recommended_cert": recommended_cert,
            "current_question": {
                "order": 1,
                "question": first_question['question'],
                "options": first_question['options'],
                "correct_answer": first_question['correct_answer']
            }
        }

        # Return formatted Bedrock Agent response
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                "apiPath": event.get('apiPath'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(response_body)
                    }
                }
            }
        }

    except ClientError as e:
        print(f"DynamoDB ClientError: {str(e)}")
        return create_error_response(event, 500, f"DynamoDB error: {str(e)}")
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(event, 500, f"Unhandled exception: {str(e)}")


def generate_questions_with_bedrock(bedrock_client, cert_name, topic, num_questions):
    """
    Generate quiz questions using Amazon Bedrock Nova Pro model
    """
    try:
        prompt = f"""You are an AWS certification exam expert. Generate {num_questions} multiple-choice questions for the {cert_name} certification exam, focusing on the topic: {topic}.

For each question, provide:
1. A clear, exam-style question
2. Exactly 4 answer options (labeled A, B, C, D)
3. The index (0-3) of the correct answer

Format your response as a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": 0
  }}
]

Requirements:
- Questions should be realistic exam-level difficulty
- Options should be plausible but only one clearly correct
- Cover different aspects of {topic}
- Return ONLY the JSON array, no additional text

Generate {num_questions} questions now:"""

        # Prepare request for Nova Pro
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 4000,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        # Invoke Bedrock model
        response = bedrock_client.converse(
            modelId="us.amazon.nova-pro-v1:0",
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )

        # Extract response text
        response_text = response['output']['message']['content'][0]['text']
        print(f"Bedrock response: {response_text}")

        # Parse JSON response
        # Clean up response in case there's markdown formatting
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        questions = json.loads(response_text)
        
        # Validate questions format
        if not isinstance(questions, list):
            print("Error: Response is not a list")
            return None
        
        for q in questions:
            if not all(key in q for key in ['question', 'options', 'correct_answer']):
                print(f"Error: Invalid question format: {q}")
                return None
            if not isinstance(q['options'], list) or len(q['options']) != 4:
                print(f"Error: Invalid options format: {q}")
                return None

        return questions

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Response text: {response_text}")
        return None
    except Exception as e:
        print(f"Error generating questions with Bedrock: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_error_response(event, status_code, error_message):
    """
    Helper function to create standardized error responses
    """
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
            "apiPath": event.get('apiPath'),
            "httpMethod": event.get('httpMethod', 'POST'),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({
                        "error": error_message
                    })
                }
            }
        }
    }
