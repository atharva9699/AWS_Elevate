import json
import boto3
import os
from decimal import Decimal
from botocore.exceptions import ClientError

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal to float"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 else int(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print("INSIDE SHOW RESULT LAMBDA FUNCTION")
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
        quiz_id = params.get('quiz_id')
        username = params.get('username')
        
        if not quiz_id:
            return create_error_response(event, 400, 'quiz_id is required')

        if not username:
            return create_error_response(event, 400, 'username is required')

        # lowercase username
        username = username.lower()

        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Get table names from environment or use defaults
        quiz_table_name = os.environ.get('QUIZ_TABLE', 'quiz')
        question_table_name = os.environ.get('QUESTION_TABLE', 'question')

        # Step 1: Fetch quiz metadata
        quiz_table = dynamodb.Table(quiz_table_name)
        
        try:
            quiz_response = quiz_table.get_item(Key={'username': username, 'id': quiz_id})
            if 'Item' not in quiz_response:
                return create_error_response(event, 404, f"Quiz '{quiz_id}' not found")
            
            quiz_data = quiz_response['Item']
            username = quiz_data.get('username')
            recommended_cert = quiz_data.get('recommended_cert')
            topic = quiz_data.get('topic')
            max_score = int(quiz_data.get('max_score', 0))
        except ClientError as e:
            print(f"Error fetching quiz: {str(e)}")
            return create_error_response(event, 500, f"Error fetching quiz: {str(e)}")

        # Step 2: Fetch all questions for this quiz
        question_table = dynamodb.Table(question_table_name)
        
        try:
            response = question_table.query(
                KeyConditionExpression='quiz_id = :quiz_id',
                ExpressionAttributeValues={':quiz_id': quiz_id}
            )
            questions = response.get('Items', [])
            
            if not questions:
                return create_error_response(event, 404, f"No questions found for quiz '{quiz_id}'")
            
            # Sort by order
            questions.sort(key=lambda x: int(x.get('order', 0)))
        except ClientError as e:
            print(f"Error fetching questions: {str(e)}")
            return create_error_response(event, 500, f"Error fetching questions: {str(e)}")

        # Step 3: Calculate score and prepare question summary
        user_score = 0
        question_summary = []
        
        for q in questions:
            correct_answer = q.get('correct_answer')
            user_answer = q.get('user_answer')
            is_correct = q.get('answered_correctly')
            
            if is_correct:
                user_score += 1
            
            question_summary.append({
                'order': q.get('order'),
                'question': q.get('question'),
                'options': q.get('options', []),
                'correct_answer': int(correct_answer) if correct_answer is not None else None,
                'user_answer': int(user_answer) if user_answer is not None else None,
                'is_correct': is_correct
            })

        # Step 4: Generate detailed explanations using Bedrock
        print(f"Generating detailed explanations for {len(questions)} questions")
        
        detailed_explanations = generate_explanations_with_bedrock(
            bedrock_runtime,
            recommended_cert,
            topic,
            question_summary
        )

        # Step 5: Identify knowledge gaps
        incorrect_questions = [q for q in question_summary if not q['is_correct']]
        knowledge_gaps = identify_knowledge_gaps(
            bedrock_runtime,
            recommended_cert,
            topic,
            incorrect_questions,
            question_summary
        )

        # Step 6: Prepare response
        percentage_score = (user_score / max_score * 100) if max_score > 0 else 0
        
        response_body = {
            "quiz_id": quiz_id,
            "username": username,
            "topic": topic,
            "recommended_cert": recommended_cert,
            "final_score": {
                "correct": user_score,
                "total": max_score,
                "percentage": round(percentage_score, 2)
            },
            "performance_summary": get_performance_summary(percentage_score),
            "detailed_explanations": detailed_explanations,
            "knowledge_gaps": knowledge_gaps,
            "quiz_statistics": {
                "total_questions": max_score,
                "correct_answers": user_score,
                "incorrect_answers": max_score - user_score,
                "accuracy_percentage": round(percentage_score, 2)
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
                        "body": json.dumps(response_body, cls=DecimalEncoder)
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


def generate_explanations_with_bedrock(bedrock_client, cert_name, topic, question_summary):
    """
    Generate detailed explanations for each question using Bedrock
    """
    try:
        # Prepare question details for Bedrock
        questions_text = ""
        for idx, q in enumerate(question_summary, start=1):
            user_answer_label = chr(65 + q['user_answer']) if q['user_answer'] is not None else "Not answered"
            correct_answer_label = chr(65 + q['correct_answer'])
            status = "✓ CORRECT" if q['is_correct'] else "✗ INCORRECT"
            
            questions_text += f"\nQuestion {idx} [{status}]:\n"
            questions_text += f"Question: {q['question']}\n"
            questions_text += f"Options:\n"
            for opt_idx, option in enumerate(q['options']):
                prefix = f"  {chr(65 + opt_idx)}. {option}"
                if opt_idx == q['user_answer']:
                    prefix += f" (User selected)"
                if opt_idx == q['correct_answer']:
                    prefix += f" (Correct)"
                questions_text += prefix + "\n"
            questions_text += "\n"

        prompt = f"""You are an expert AWS certification instructor. Analyze the quiz responses below for the {cert_name} certification, Topic: {topic}.

{questions_text}

For EACH question that was answered INCORRECTLY, provide:
1. Why the correct answer is correct (detailed explanation)
2. Why the user's selected answer is incorrect (if they selected one)
3. Key concepts to understand

Format your response as a JSON array with this structure:
[
  {{
    "question_number": 1,
    "is_correct": false,
    "question_text": "The question",
    "correct_answer": "The correct option text",
    "user_selected": "What the user selected (or null)",
    "explanation": {{
      "why_correct": "Detailed explanation of why the correct answer is right",
      "why_incorrect": "Explanation of why the user's answer was incorrect",
      "key_concepts": ["concept1", "concept2", "concept3"]
    }}
  }}
]

Return ONLY valid JSON array, no additional text."""

        print(f"Bedrock explanations prompt: {prompt}")

        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 8000,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        response = bedrock_client.converse(
            modelId="us.amazon.nova-pro-v1:0",
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )

        response_text = response['output']['message']['content'][0]['text']
        print(f"Bedrock explanations response: {response_text[:500]}...")

        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        explanations = json.loads(response_text)
        
        if not isinstance(explanations, list):
            print("Error: Explanations response is not a list")
            return []
        
        return explanations

    except json.JSONDecodeError as e:
        print(f"JSON parsing error in explanations: {str(e)}")
        return []
    except Exception as e:
        print(f"Error generating explanations with Bedrock: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def identify_knowledge_gaps(bedrock_client, cert_name, topic, incorrect_questions, all_questions):
    """
    Identify knowledge gaps and recommend learning areas
    """
    try:
        if not incorrect_questions:
            return {
                "overall_assessment": "Excellent! You answered all questions correctly.",
                "gaps": [],
                "recommendations": []
            }

        # Prepare incorrect questions summary
        incorrect_summary = ""
        for q in incorrect_questions:
            incorrect_summary += f"- {q['question'][:100]}... (Topic: {topic})\n"

        prompt = f"""You are an AWS certification advisor for the {cert_name} certification.

The user scored incorrectly on these topics within {topic}:
{incorrect_summary}

Based on their incorrect answers, provide:
1. Specific knowledge gaps they should address
2. Recommended learning topics and AWS services to study
3. Study priorities (most important first)

Format your response as JSON:
{{
  "overall_assessment": "Brief assessment of their knowledge level",
  "gaps": [
    {{
      "gap": "Specific knowledge gap",
      "severity": "high/medium/low",
      "aws_service": "Relevant AWS service",
      "description": "Why this matters for the certification"
    }}
  ],
  "recommendations": [
    {{
      "topic": "Topic to study",
      "priority": 1,
      "learning_resources": "What to focus on",
      "practice_area": "Specific area to practice"
    }}
  ]
}}

Return ONLY valid JSON, no additional text."""

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

        response = bedrock_client.converse(
            modelId="us.amazon.nova-pro-v1:0",
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )

        response_text = response['output']['message']['content'][0]['text']
        
        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        knowledge_gaps = json.loads(response_text)
        return knowledge_gaps

    except json.JSONDecodeError as e:
        print(f"JSON parsing error in knowledge gaps: {str(e)}")
        return {"gaps": [], "recommendations": []}
    except Exception as e:
        print(f"Error identifying knowledge gaps: {str(e)}")
        return {"gaps": [], "recommendations": []}


def get_performance_summary(percentage_score):
    """
    Generate a performance summary based on score
    """
    if percentage_score >= 90:
        return "Excellent! You're well-prepared for this topic."
    elif percentage_score >= 75:
        return "Good performance! A few areas to review before the exam."
    elif percentage_score >= 60:
        return "Fair performance. Focus on the knowledge gaps identified below."
    else:
        return "Needs improvement. Review the explanations and study the recommended topics."


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
