import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        print("INSIDE LAMBDA FUNCTION")
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

        # Check required username
        username = params.get('username')
        if not username:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'username is required'})
            }

        # Allowed update fields
        allowed_fields = ['aspiringjobrole', 'clearedcertifications', 'currentjobrole', 'interestareas','recommended_cert']
        update_expr = []
        expr_attr_values = {}

        for field in allowed_fields:
            if field in params:
                update_expr.append(f"{field} = :{field}")
                expr_attr_values[f":{field}"] = params[field]

        if not update_expr:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No valid fields to update'})
            }

        # DynamoDB table from environment or default
        table_name = os.environ.get('DYNAMODB_TABLE', 'user_profile')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        # Update the user profile
        response = table.update_item(
            Key={'username': username},
            UpdateExpression="SET " + ", ".join(update_expr),
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="UPDATED_NEW"
        )

        updated_attributes = response.get("Attributes", {})

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
                        "body": json.dumps({
                            "message": "User profile updated successfully!",
                            "updatedAttributes": updated_attributes
                        })
                    }
                }
            }
        }

    except ClientError as e:
        print(f"DynamoDB ClientError: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"DynamoDB error: {str(e)}"})
        }
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Unhandled exception: {str(e)}"})
        }  
