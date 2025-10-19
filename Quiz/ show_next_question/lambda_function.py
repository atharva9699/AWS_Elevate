import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        print("INSIDE SHOW NEXT QUESTION LAMBDA FUNCTION")
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
        current_order = params.get('current_order')
        user_answer = params.get('user_answer')
        username = params.get('username')

        if not quiz_id:
            return create_error_response(event, 400, 'quiz_id is required')
        if not username:
            return create_error_response(event, 400, 'username is required')
        if not current_order:
            return create_error_response(event, 400, 'current_order is required')
        if user_answer is None:
            return create_error_response(event, 400, 'user_answer is required')

        # lowercase username
        username = username.lower()
        
        # Convert current_order to integer for calculations
        try:
            current_order_int = int(current_order)
        except ValueError:
            return create_error_response(event, 400, 'current_order must be a valid number')

        # Convert user_answer (A, B, C, D) to index (0, 1, 2, 3)
        user_answer_upper = str(user_answer).upper().strip()
        answer_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        
        if user_answer_upper in answer_map:
            user_answer_index = answer_map[user_answer_upper]
        else:
            # Try to parse as integer directly
            try:
                user_answer_index = int(user_answer)
                if user_answer_index not in [0, 1, 2, 3]:
                    return create_error_response(event, 400, 'user_answer must be A, B, C, D or 0-3')
            except ValueError:
                return create_error_response(event, 400, 'user_answer must be A, B, C, D or 0-3')

        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        
        # Get table names from environment or use defaults
        quiz_table_name = os.environ.get('QUIZ_TABLE', 'quiz')
        question_table_name = os.environ.get('QUESTION_TABLE', 'question')

        question_table = dynamodb.Table(question_table_name)
        quiz_table = dynamodb.Table(quiz_table_name)

        # Step 1: Get the current question to check the answer
        try:
            current_question_response = question_table.get_item(
                Key={
                    'quiz_id': quiz_id,
                    'order': str(current_order_int)
                }
            )
            
            if 'Item' not in current_question_response:
                return create_error_response(event, 404, f"Question with order {current_order_int} not found for quiz {quiz_id}")
            
            current_question = current_question_response['Item']
            correct_answer = int(current_question['correct_answer'])
            
        except ClientError as e:
            print(f"Error fetching current question: {str(e)}")
            return create_error_response(event, 500, f"Error fetching current question: {str(e)}")

        # Step 2: Check if the answer is correct and update the current question
        is_correct = (user_answer_index == correct_answer)
        user_score = 1 if is_correct else 0
        
        try:
            question_table.update_item(
                Key={
                    'quiz_id': quiz_id,
                    'order': str(current_order_int)
                },
                UpdateExpression='SET user_score = :score, answered_correctly = :correct, user_answer = :user_answer',
                ExpressionAttributeValues={
                    ':score': user_score,
                    ':correct': is_correct,
                    ':user_answer': user_answer_index
                }
            )
            print(f"Updated question {current_order_int}: user_score={user_score}, answered_correctly={is_correct}")
        except ClientError as e:
            print(f"Error updating current question: {str(e)}")
            return create_error_response(event, 500, f"Error updating question: {str(e)}")

        # Step 3: Update quiz table with cumulative score
        try:
            # Get current quiz to update total user_score
            quiz_response = quiz_table.get_item(Key={
                    'username': username,
                    'id': quiz_id
                })
            
            if 'Item' not in quiz_response:
                return create_error_response(event, 404, f"Quiz {quiz_id} not found")
            
            quiz_item = quiz_response['Item']
            current_total_score = int(quiz_item.get('user_score', 0))
            new_total_score = current_total_score + user_score
            
            quiz_table.update_item(
                Key={
                    'username': username,
                    'id': quiz_id
                },
                UpdateExpression='SET user_score = :score',
                ExpressionAttributeValues={
                    ':score': new_total_score
                }
            )
            print(f"Updated quiz total score: {new_total_score}")
            
            max_score = int(quiz_item.get('max_score', 0))
            
        except ClientError as e:
            print(f"Error updating quiz score: {str(e)}")
            return create_error_response(event, 500, f"Error updating quiz score: {str(e)}")

        # Step 4: Get the next question
        next_order = current_order_int + 1
        
        try:
            next_question_response = question_table.get_item(
                Key={
                    'quiz_id': quiz_id,
                    'order': str(next_order)
                }
            )
            
            if 'Item' not in next_question_response:
                # No more questions - quiz is complete
                response_body = {
                    "quiz_id": quiz_id,
                    "previous_question_correct": is_correct,
                    "correct_answer": correct_answer,
                    "quiz_complete": True,
                    "message": f"Quiz completed! You've answered all {current_order_int} questions.",
                    "final_score": new_total_score,
                    "max_score": max_score
                }
                
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
            
            next_question = next_question_response['Item']
            
        except ClientError as e:
            print(f"Error fetching next question: {str(e)}")
            return create_error_response(event, 500, f"Error fetching next question: {str(e)}")

        # Step 5: Prepare response with next question
        response_body = {
            "quiz_id": quiz_id,
            "previous_question_correct": is_correct,
            "correct_answer": correct_answer,
            "quiz_complete": False,
            "current_question": {
                "order": next_order,
                "question": next_question['question'],
                "options": next_question['options']
            },
            "progress": {
                "current_question": next_order,
                "total_questions": max_score,
                "current_score": new_total_score
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
