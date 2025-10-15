import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        print("INSIDE GET CERT INFO LAMBDA FUNCTION")
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

        # Check required parameter
        username = params.get('username')
        
        if not username:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'username is required'})
            }

        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        
        # Step 1: Lookup user_profile table
        user_profile_table = dynamodb.Table('user_profile')
        user_response = user_profile_table.get_item(
            Key={'username': username}
        )
        
        if 'Item' not in user_response:
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                    "apiPath": event.get('apiPath'),
                    "httpMethod": event.get('httpMethod', 'GET'),
                    "httpStatusCode": 404,
                    "responseBody": {
                        "application/json": {
                            "body": json.dumps({
                                "error": f"User with username '{username}' not found"
                            })
                        }
                    }
                }
            }
        
        # Get recommended_cert from user profile
        recommended_cert = user_response['Item'].get('recommended_cert')
        
        if not recommended_cert:
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                    "apiPath": event.get('apiPath'),
                    "httpMethod": event.get('httpMethod', 'GET'),
                    "httpStatusCode": 404,
                    "responseBody": {
                        "application/json": {
                            "body": json.dumps({
                                "error": f"No recommended certification found for user '{username}'"
                            })
                        }
                    }
                }
            }
        
        # Step 2: Lookup CertInfo table
        cert_info_table = dynamodb.Table('CertInfo')
        cert_response = cert_info_table.get_item(
            Key={'CertificationName': recommended_cert}
        )
        
        if 'Item' not in cert_response:
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                    "apiPath": event.get('apiPath'),
                    "httpMethod": event.get('httpMethod', 'GET'),
                    "httpStatusCode": 404,
                    "responseBody": {
                        "application/json": {
                            "body": json.dumps({
                                "error": f"Certification '{recommended_cert}' not found in CertInfo table"
                            })
                        }
                    }
                }
            }
        
        # Step 3: Return the entire CertInfo record
        cert_info = cert_response['Item']
        
        # Return formatted Bedrock Agent response
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                "apiPath": event.get('apiPath'),
                "httpMethod": event.get('httpMethod', 'GET'),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": cert_info
                    }
                }
            }
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"DynamoDB ClientError: {str(e)}")
        
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                "apiPath": event.get('apiPath'),
                "httpMethod": event.get('httpMethod', 'GET'),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({'error': f"DynamoDB error: {str(e)}"})
                    }
                }
            }
        }
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'UnknownActionGroup'),
                "apiPath": event.get('apiPath'),
                "httpMethod": event.get('httpMethod', 'GET'),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({'error': f"Unhandled exception: {str(e)}"})
                    }
                }
            }
        }
