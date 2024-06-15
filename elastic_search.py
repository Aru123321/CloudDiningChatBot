from elasticsearch import Elasticsearch, helpers
import json
import os

# Function to read JSON file
def read_json_file(file_path):
    with open(file_path, 'r') as file:
            data = json.load(file)
            for record in data:     
                yield json.dumps(record)

# Function to get all indices
def get_all_indices():
    resp = client.indices.get("*")
    return resp

# Function to bulk load data
def bulk_load_data(es_client, index_name, data):
    actions = []
    for doc in data:
        action = {
            "_index": index_name,
            "_source": doc
        }
        actions.append(action)
    
    helpers.bulk(es_client, actions)


# Replace these with your Elasticsearch server details
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST")
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")

ELASTICSEARCH_PORT = 443  # Replace with your port if different
INDEX_NAME = "restaurant-data"

# Path to your JSON file
FILE_PATH = 'restaurants.json'
data = read_json_file(FILE_PATH)

client = Elasticsearch(
    ELASTICSEARCH_HOST,
    http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
)

if not client.indices.exists(index=INDEX_NAME):
    client.indices.create(index=INDEX_NAME)
    print(f"Index {INDEX_NAME} created.")
else:
    print(f"Index {INDEX_NAME} already exists.")

# Load data into Elasticsearch
bulk_load_data(client, INDEX_NAME, data)
print(f"Data successfully loaded into index {INDEX_NAME}.")