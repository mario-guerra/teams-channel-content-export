'''
This script fetches and formats messages and their replies from Microsoft Teams using the Microsoft Graph API.
It uses an access token, group id, and channel id read from a .env file.
The script cleans the HTML content of the messages, formats the messages and their replies into a JSON structure,
and prints the formatted messages.

The script fetches all messages and their replies from the specified channel and then filters the messages by date in Python. We have to filter after fetching all the contents because the Microsoft Graph API does not currently support the createdDateTime filter query parameter for the /messages endpoint.
The date filter in Python skips any messages that were created before the specified date.

To run this script:
1. Ensure that you have Python 3 and the required packages (requests, json, html, re, bs4, python-dotenv) installed.
2. Obtain an access token by logging in to the Graph Explorer (https://developer.microsoft.com/en-us/graph/graph-explorer) and copying the token from the 'Access token' panel. This token has a short lifespan, so expect to regen it often.
3. Replace the values in the .env file with your actual ACCESS_TOKEN, GROUP_ID, and CHANNEL_ID.
4. Save the .env file in the same directory as this script.
5. Run the script using the command: python channel_query.py <output_file.json> <date_from>

Author: Mario Guerra
License: MIT
'''

import os
import requests
import json
import html
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access token value was cribbed from the Graph Explorer UI after I signed in. The token has a short half life, so expect to regen it often.
access_token = os.getenv('ACCESS_TOKEN')

# Get the group_id and channel_id from the environment variables
group_id = os.getenv('GROUP_ID')
channel_id = os.getenv('CHANNEL_ID')

# Check if a date was provided as a command line argument
if len(sys.argv) > 2:
    # Parse the date from the command line argument and set the time to '00:00:00'
    date_from = datetime.strptime(sys.argv[2] + 'T00:00:00', '%Y-%m-%dT%H:%M:%S')
else:
    # Default to today's date if no date was provided and set the time to '00:00:00'
    date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Get the messages and their replies
url = f'https://graph.microsoft.com/beta/teams/{group_id}/channels/{channel_id}/messages?$expand=replies'
headers = {'Authorization': 'Bearer ' + access_token}

# Initialize the list of formatted messages
formatted_messages = []

# Iterate over the pages of messages
while url:
    response = requests.get(url, headers=headers)
    # print("Status code:", response.status_code)
    # print("Response text:", response.text)
    data = response.json()

    # Save @odata.count and @odata.nextLink if they exist
    # for use in iterating over the pages of messages
    odata_count = data.get('@odata.count')
    odata_nextLink = data.get('@odata.nextLink')

    messages = data.get('value', [])

    for message in messages:
        # Convert the message's createdDateTime to a datetime object without fractional seconds
        # Convert the message's createdDateTime to a date object
        message_date = datetime.strptime(message['createdDateTime'].split('T')[0], '%Y-%m-%d').date()

        # print("Message Date: ", message_date)
        # print("Date From: ", date_from)

        # Skip this message if it's older than the specified date
        if message_date < date_from.date():
            continue

        # Clean the HTML from the message content
        message_content = html.unescape(message['body']['content']) if message['body']['content'] else ''
        message_content = message_content.replace('\u00a0', ' ')

        # Parse the message content as HTML
        soup = BeautifulSoup(message_content, 'html.parser')

        # For each <a> tag in the message content
        for a_tag in soup.find_all('a'):
            # If the <a> tag has an href attribute
            if 'href' in a_tag.attrs:
                # Replace the <a> tag with its href attribute formatted as a Markdown link
                a_tag.replace_with(f"[{a_tag.text}]({a_tag['href']})")

        # Convert the parsed HTML back to a string and remove all HTML tags
        message_content = re.sub('<[^<]+?>', '', str(soup))

        # Format the message and its replies
        formatted_message = {
            "messageId": message['id'],
            "messageDateTime": message['createdDateTime'],
            "messageContent": message_content,
            "replies": [
                {
                    "replyId": reply['id'],
                    "replyDateTime": reply['createdDateTime'],
                    "replyContent": (re.sub('<[^<]+?>', '', html.unescape(reply['body']['content'])) if reply['body']['content'] else '').replace('\u00a0', ' ')
                }
                for reply in message['replies']
            ]
        }

        # Add the formatted message to the list
        formatted_messages.append(formatted_message)

    # Update the URL to the next page URL
    url = odata_nextLink

# Print the formatted messages as JSON
json_output = json.dumps({"messages": formatted_messages}, indent=2)
print(json_output)

# Check if a file name was provided as a command line argument
if len(sys.argv) > 1:
    # Write the output to the file
    with open(sys.argv[1], 'w') as f:
        print(json_output, file=f)