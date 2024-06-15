import requests
import boto3
from datetime import datetime
from decimal import Decimal

# Yelp API configuration
API_KEY = '7AqA2PgBSzm2NetAIqKar7_eqNhhFg2Vhm5MinoW-OEFj63Pyy7KJ9tndg4HbKtqEPosZ1Qrxi09BjZWbShreXYGk5vk4glVFKGmXGw80tkcSJEhPWxrJPjd4-NhZnYx'
HEADERS = {'Authorization': f'Bearer {API_KEY}'}
SEARCH_URL = 'https://api.yelp.com/v3/businesses/search'

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace 'your-region' with your DynamoDB region
table = dynamodb.Table('yelp-rest')

def fetch_restaurants(cuisine_type, location='Boston', limit=50, offset=0):
    params = {
        'term': cuisine_type,
        'location': location,
        'limit': limit,
        'offset': offset
    }
    response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    return response.json().get('businesses', [])

def store_in_dynamodb(restaurants):
    print("Storing in dynamodb")
    for restaurant in restaurants:
        item = {
            'BusinessID': restaurant['id'],
            'Name': restaurant['name'],
            'Address': ", ".join(restaurant['location']['display_address']),
            'Coordinates': {
                'Latitude': Decimal(str(restaurant['coordinates']['latitude'])),
                'Longitude': Decimal(str(restaurant['coordinates']['longitude']))
            },
            'NumberOfReviews': Decimal(restaurant['review_count']),
            'Rating': Decimal(str(restaurant['rating'])),
            'ZipCode': restaurant['location']['zip_code'],
            'InsertedAtTimestamp': str(datetime.now())
        }
        table.put_item(Item=item)

if __name__ == '__main__':
    cuisine_types = ['Indian', 'Italian', 'Mexican', 'Japanese', 'American']
    total_stored_restaurants = 0
    max_total_restaurants = 100

    for cuisine in cuisine_types:
        if total_stored_restaurants >= max_total_restaurants:
            break

        total_restaurants = []
        for offset in range(0, 1000, 50):
            if len(total_restaurants) >= 50:
                break
            restaurants = fetch_restaurants(cuisine_type=cuisine, location='Boston', limit=50, offset=offset)
            if not restaurants:
                break
            total_restaurants.extend(restaurants)
            if len(total_restaurants) >= 50:
                total_restaurants = total_restaurants[:50]
                break

        if total_stored_restaurants + len(total_restaurants) > max_total_restaurants:
            total_restaurants = total_restaurants[:max_total_restaurants - total_stored_restaurants]

        store_in_dynamodb(total_restaurants)
        total_stored_restaurants += len(total_restaurants)

        if total_stored_restaurants >= max_total_restaurants:
            break
