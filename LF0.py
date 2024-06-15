import json
import boto3

# Initialize Lex client
lex_client = boto3.client('lex-runtime')

def process_message(message):
    # Assuming 'message' contains the text to send to Lex
    lex_response = lex_client.post_text(
        botName='DiningConciergeBot',  # Replace with your Lex bot's name
        botAlias='botfirst',  # Replace with your Lex bot's alias
        userId='12345',  # Unique ID for the user session
        inputText=message
    )

    print("Lex response:", lex_response)  # Debugging: print the response from Lex

    # Format the response from Lex
    return {
        "type": "unstructured",
        "unstructured": {
            "id": "unique-id",  # Generate or modify this as necessary
            "text": lex_response['message'],  # Message from Lex
            "timestamp": "timestamp"  # Add current timestamp or modify as needed
        }
    }

def lambda_handler(event, context):
    try:
        print("Event:", event)  # Debugging: print the incoming event

        body = event.get("messages")
        # body = json.loads(body)
        
        # # Check if the body is structured as expected
        # if not body or "messages" not in body or not body["messages"]:
        #     return {
        #         "statusCode": 400,
        #         "body": json.dumps({"error": "Invalid request format"})
        #     }
        
        # Assuming there's at least one message
        response_messages = [process_message(body[0]["unstructured"]["text"])]
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": json.dumps({"messages": response_messages}),
        }
    
    except Exception as e:
        print("Error:", e)  # Debugging: print the error
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
        