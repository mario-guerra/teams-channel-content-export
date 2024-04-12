"""
Python Script: convert_channel_data.py

This script extracts question-answer pairs from a given JSON data file and creates a new JSON file for each pair. 
It uses the OpenAI API to generate questions and answers based on the input data.

The script accepts two command-line arguments:
1. 'input_file': The path to the input JSON file.
2. 'output_dir': The path to the output directory where the question-answer pair files will be saved.

The script uses environment variables for OpenAI API configuration, which should be set in a .env file:
1. 'AZURE_OPENAI_API_KEY': The OpenAI API key.
2. 'AZURE_OPENAI_ENDPOINT': The OpenAI API endpoint.
3. 'AZURE_OPENAI_DEPLOYMENT_NAME': The name of the OpenAI deployment.

How to run:
1. Ensure that all the necessary Python libraries are installed and the .env file is set up correctly.
2. Run the script from the command line with the input file and output directory as arguments. 
   For example: python convert_channel_data.py input.json output_dir

Author: Mario Guerra
License: MIT
"""

import json
import os
import re
import argparse
import openai
import asyncio

from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_type = "azure"
openai.api_version = os.get("AZURE_OPENAI_API_VERSION")

# # Define a prompt for OpenAI API to generate questions and 
question_prompt = """Given the following input, extract and summarize the questions being asked. Clean up the formatting to remove extraneous characters and improve readability. Distill each question down to the essence of what is being asked, removing extraneous information and formatting. Do not include anyone's names in the output. Format the output using the following template, with each question forming a unique item as shown in the example below:
[
  {
    "question": "How do we specify the naming of the SDK's through TypeSpec?"
  },
  {
    "question": "Is the naming of the package related to the names of the folders in the folder structure?"
  },
  ...
"""

answers_prompt = """Given the following question and answers, extract and synthesize the answers to the question being asked. Create a single concise and correct answer for each question from all answers provided. If an answer includes a name, rephrase it to avoid using the name. Clean up the formatting to improve readability. Format the output using the following template, with each question forming a unique item as shown in the example below:
[
  {
    "answer": "Specify the name via the `name` field in the `TypeSpec`."
  },
  ...
"""

# Check if a string is a valid JSON object
def is_valid_json(json_string):
    try:
        json.loads(json_string)
        return True
    except ValueError:
        print("Invalid JSON:", json_string)
        return False

# Generate questions and answers: generate_qna() is an async 
# function that sends request to OpenAI API to generate QnA based on input.
# Retries request if response is invalid, up to a maximum number of attempts.
async def generate_qna(input, prompt):
    max_retries = 3
    retry_count = 0
    retry_delay = 2  # Delay between retries in seconds
    system_prompt = prompt

    while retry_count < max_retries:
        try:
            print(f"Attempt {retry_count + 1} of {max_retries}...")
            response = openai.ChatCompletion.create(
                engine=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input},
                ],
                max_tokens=4096,
                n=1,
                stop=None,
                temperature=0.1,
                top_p=0.1,
            )
            return response.choices[0].message.content
        except openai.error.Timeout:
            if retry_count < max_retries - 1:  # If we haven't reached the maximum number of retries
                print(f"Request timed out, retrying (attempt {retry_count + 1})...")
                await asyncio.sleep(retry_delay)  # Wait before retrying
                continue  # Retry the request
            else:  # If we've reached the maximum number of retries
                print(f"Request timed out after {max_retries} attempts. Skipping Q&A for this chunk.")
                return "{}"  # Return an empty JSON string as a fallback
        except Exception as e:  # Catch all other exceptions
                error_message = str(e)
                delay_str = re.search(r'Please retry after (\d+)', error_message)
                if delay_str:
                    delay = int(delay_str.group(1))
                    print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    retry_count += 1
                else:
                    print(f"An error occurred: {e}")
                    return "{}"  # Return an empty JSON string as a fallback
        
        retry_count += 1

        if retry_count < max_retries - 1:
            await asyncio.sleep(retry_delay)

    print(f"Failed to get a valid response after {max_retries} attempts. Skipping Q&A for this chunk.")
    return "{}"  # Return an empty JSON string as a fallback

async def extract_qa_pairs(input_file, output_dir):
    with open(input_file, 'r') as f:
        data = json.load(f)

    counter = 0  # Initialize the counter

    for item in data['messages']:
        # Skip this message if there are no replies
        if not item['replies']:
            print("No replies to message, skipping messageId ", item['messageId'])
            continue
        message_id = item['messageId']
        message_content = item['messageContent']
        replies = item['replies']
        answers = [reply['replyContent'] for reply in replies]
        answer_content = ' '.join(answers)

        questions = await generate_qna(message_content, question_prompt)
        answers = await generate_qna(questions + '\n' + answer_content, answers_prompt)
        print("Message ID:", message_id)
        print("Questions:", questions)
        print("Answers:", answers)

        # Create a dictionary for this pair of questions and answers
        if (is_valid_json(questions) and is_valid_json(answers)):
            question_list = json.loads(questions)
            question_list = [{"Q" + str(counter): question["question"]} for question in question_list]
            answer_list = [{"A" + str(counter): answer["answer"]} for answer in json.loads(answers)]
                
            pair = {
                "Questions": question_list,
                "Answers": answer_list
            }

            # Create a new file for each pair
            with open(os.path.join(output_dir, f'qna_{counter}.json'), 'w') as f:
                f.write(json.dumps(pair, indent=4))

            counter += 1  # Increment the counter
        else:
            print("Invalid JSON returned from chat function, skipping this pair.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract question/answer pairs from JSON data.')
    parser.add_argument('input_file', type=str, help='Path to the input JSON file.')
    parser.add_argument('output_dir', type=str, help='Path to the output directory.')

    args = parser.parse_args()

    asyncio.run(extract_qa_pairs(args.input_file, args.output_dir))