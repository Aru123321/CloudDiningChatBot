import json
import boto3
import os
from elasticsearch import Elasticsearch, helpers

# Initialize AWS clients
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

# Configuration

queue_url = os.environ.get("QUEUE_URL")
table_name = os.environ.get("TABLE_NAME")
email_source = os.environ.get("EMAIL_SOURCE")

# ElasticSearch Stuff
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST")
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")

ELASTICSEARCH_PORT = 443  # Replace with your port if different
INDEX_NAME = "restaurant-data"


es = Elasticsearch(
    ELASTICSEARCH_HOST, http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
)


def lambda_handler(event, context):
    # Step 1: Receive message from SQS
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    if not messages:
        return {"statusCode": 200, "body": json.dumps("No messages in the queue")}

    message = messages[0]
    receipt_handle = message["ReceiptHandle"]
    data = json.loads(message["Body"])

    cuisine = data.get("Cuisine", "Unknown")
    email = data.get("Email", "")

    if not email:
        print("No email address provided")
        return {
            "statusCode": 400,
            "body": json.dumps("Invalid message: No email address found"),
        }

    # Step 2: Query Elasticsearch for restaurant suggestions
    suggestions = get_restaurant_suggestions(cuisine)

    if not suggestions:
        print(f"No restaurant suggestions found for cuisine: {cuisine}")
        return {
            "statusCode": 200,
            "body": json.dumps(f"No suggestions available for {cuisine}"),
        }

    # Step 3: Fetch detailed restaurant information from DynamoDB
    detailed_suggestions = [get_restaurant_details(s) for s in suggestions]

    # Step 4: Format email content
    email_content = format_email(detailed_suggestions)

    # Step 5: Send email via SES
    send_email(email, email_content)

    # Step 6: Delete the processed message from the SQS queue
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

    return {"statusCode": 200, "body": json.dumps("Suggestions sent successfully")}


def get_restaurant_suggestions(cuisine):

    try:
        search_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "multi_match": {
                                "type": "best_fields",
                                "query": cuisine,
                            }
                        }
                    ],
                    "should": [],
                    "must_not": [],
                }
            }
        }

        response = es.search(index=INDEX_NAME, body=search_query)
        hits = response["hits"]["hits"]
        return [hit["_source"]["BusinessID"] for hit in hits]

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return []


def get_restaurant_details(restaurant_id):
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(Key={"BusinessID": restaurant_id})
        return response.get("Item", {})
    except Exception as e:
        print(f"Error retrieving data from DynamoDB: {e}")
        return {}


def format_email(suggestions):
    email_content = "Here are your restaurant suggestions:\n"
    for restaurant in suggestions:
        name = restaurant.get("Name", "N/A")
        address = restaurant.get("Address", "N/A")
        email_content += f"- {name}, located at {address}\n"
    return email_content


def send_email(recipient, content):
    try:
        response = ses.send_email(
            Source=email_source,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "Your Restaurant Suggestions"},
                "Body": {"Text": {"Data": content}},
            },
        )
        print(f"Email sent successfully to {recipient}: {response}")
    except Exception as e:
        print(f"Error sending email via SES: {e}")
