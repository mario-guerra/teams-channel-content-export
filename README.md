# Microsoft Teams Channel Data Export for RAG-Enhanced Chatbot

This repository contains three Python scripts that facilitate the extraction of data from Microsoft Teams channels and its transformation into question-answer pairs for use in a Retrieval-Augmented Generation (RAG) enhanced chatbot.

To learn how to use Teams channel data to power a smart chatbot, check out the related [blog post](https://marioguerra.xyz/building-intelligent-chatbots-with-microsoft-teams-data/).

## Overview

The `channel_query.py` script fetches and formats messages and their replies from Microsoft Teams using the Microsoft Graph API. The `convert_channel_data_json.py` script takes the JSON output file produced by the `channel_query.py` script and extracts question-answer pairs, creating a new JSON file for each pair using Azure OpenAI. The `convert_channel_data_markdown.py` script performs a similar function but generates the question-answer pairs as markdown, with the question set as a heading and the answer as content following the heading.

## Prerequisites

- Python 3
- Required Python packages: `requests`, `json`, `html`, `re`, `bs4`, `python-dotenv`, `openai`, `argparse`, `asyncio`
- Access to Microsoft Graph API and Azure OpenAI

## Setup

1. Clone the repository to your local machine.
2. Install the required Python packages.
3. Obtain an access token from the [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer).
4. Replace the values in the .env file with your actual `ACCESS_TOKEN`, `GROUP_ID`, and `CHANNEL_ID`, as well as your Azure OpenAI endpoint, API key, deployment, and API version.
5. Save the .env file in the same directory as the scripts.

## Usage

### channel_query.py

This script fetches and formats messages and their replies from Microsoft Teams using the Microsoft Graph API. It cleans the HTML content of the messages and formats them into a JSON structure.

To run the script, use the command: `python channel_query.py <output_file.json> <date_from as YYYY-MM-DD>`

### convert_channel_data_json.py

This script extracts question-answer pairs from a given JSON data file and creates a new JSON file for each pair. It uses the OpenAI API to generate questions and answers based on the input data.

To run the script, use the command: `python convert_channel_data.py <input_file.json> <output_dir>`

### convert_channel_data_markdown.py

This script extracts question-answer pairs from a given JSON data file and creates a new markdown file for each pair. It uses the OpenAI API to generate questions and answers based on the input data. The question is set as a heading and the answer as content following the heading in the markdown file.

To run the script, use the command: `python convert_channel_data_markdown.py <input_file.json> <output_dir>`

## License

MIT
