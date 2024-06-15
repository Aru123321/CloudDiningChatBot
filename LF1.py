import json
import boto3
import logging
import os

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the SQS client
sqs = boto3.client('sqs')
queue_url = os.environ.get("QUEUE_URL")

def lambda_handler(event, context):
    try:
        intent_name = event['currentIntent']['name']
        
        if intent_name == 'GreetingIntent':
            return handle_greeting_intent(event)
        elif intent_name == 'ThankYouIntent':
            return handle_thank_you_intent(event)
        elif intent_name == 'DiningSuggestionsIntent':
            return handle_dining_suggestions_intent(event)
        else:
            return default_response()
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return handle_error(e)

def handle_greeting_intent(event):
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "Hi there, how can I help?"
            }
        }
    }
    return response

def handle_thank_you_intent(event):
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "You're welcome!"
            }
        }
    }
    return response

def handle_dining_suggestions_intent(event):
    slots = event['currentIntent']['slots']
    location = slots['Location']
    cuisine = slots['Cuisine']
    dining_time = slots['DiningTime']
    number_of_people = slots['NumberOfPeople']
    email = slots['Email']
    
    if not location or not cuisine or not dining_time or not number_of_people or not email:
        return elicit_slot(event, location, cuisine, dining_time, number_of_people, email)
    
    # Log the collected information
    logger.info(f"Collected info - Location: {location}, Cuisine: {cuisine}, DiningTime: {dining_time}, NumberOfPeople: {number_of_people}, Email: {email}")
    
    # Push to SQS
    try:
        message_body = json.dumps({
            'Location': location,
            'Cuisine': cuisine,
            'DiningTime': dining_time,
            'NumberOfPeople': number_of_people,
            'Email': email
        })
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        
        logger.info(f"Message sent to SQS: {message_body}")
        
        response = {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": f"Got it! I will send dining suggestions for {cuisine} cuisine in {location} at {dining_time} for {number_of_people} people to {email}. You will receive an email with the suggestions shortly."
                }
            }
        }
        return response
    except Exception as e:
        logger.error(f"Error sending message to SQS: {str(e)}", exc_info=True)
        return handle_error(e)

def elicit_slot(event, location, cuisine, dining_time, number_of_people, email):
    slots = event['currentIntent']['slots']
    if not location:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "intentName": event['currentIntent']['name'],
                "slots": slots,
                "slotToElicit": "Location",
                "message": {"contentType": "PlainText", "content": "Which city or area are you looking to dine in?"}
            }
        }
    elif not cuisine:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "intentName": event['currentIntent']['name'],
                "slots": slots,
                "slotToElicit": "Cuisine",
                "message": {"contentType": "PlainText", "content": "What type of cuisine would you like to try?"}
            }
        }
    elif not dining_time:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "intentName": event['currentIntent']['name'],
                "slots": slots,
                "slotToElicit": "DiningTime",
                "message": {"contentType": "PlainText", "content": "What time would you like to dine?"}
            }
        }
    elif not number_of_people:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "intentName": event['currentIntent']['name'],
                "slots": slots,
                "slotToElicit": "NumberOfPeople",
                "message": {"contentType": "PlainText", "content": "How many people are in your party?"}
            }
        }
    elif not email:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "intentName": event['currentIntent']['name'],
                "slots": slots,
                "slotToElicit": "Email",
                "message": {"contentType": "PlainText", "content": "Can you provide your email address for the reservation?"}
            }
        }

def handle_error(e):
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Failed",
            "message": {
                "contentType": "PlainText",
                "content": f"An error has occurred: {str(e)}"
            }
        }
    }
    return response

def default_response():
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "I'm still under development. Please come back later."
            }
        }
    }
    return response
