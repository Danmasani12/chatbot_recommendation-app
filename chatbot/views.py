from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    logging.error("OpenAI API key is not set. Please add it to your .env file.")
else:
    openai.api_key = OPENAI_API_KEY


@csrf_exempt
def get_response(request):
    
    if request.method == 'POST':
        try:
            # Parse JSON payload
            data = json.loads(request.body.decode('utf-8'))
            user_input = data.get('message')

            if not user_input:
                logging.warning("Empty 'message' field in the request.")
                return JsonResponse({"error": "Message field is required"}, status=400)

            logging.info(f"Received user input: {user_input}")

            # Call OpenAI ChatCompletion API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": f"Answer the following question and provide references: {user_input}"
                    },
                ],
                max_tokens=300,
            )

            # Extract reply and references from the API response
            reply = response['choices'][0]['message']['content'].strip()
            logging.info(f"Generated reply: {reply}")

            # Attempt to extract references if formatted in the response
            # Assuming the AI includes references in the reply in a JSON-like format
            try:
                split_reply = reply.split("References:")
                answer = split_reply[0].strip()
                references_text = split_reply[1].strip() if len(split_reply) > 1 else "No references provided."
                
                references = [
                    {"title": ref.split("-")[0].strip(), "url": ref.split("-")[1].strip()}
                    for ref in references_text.split("\n") if "-" in ref
                ]
            except Exception as parse_error:
                logging.warning(f"Failed to parse references: {parse_error}")
                references = []

            return JsonResponse({
                "response": answer,
                "references": references
            })
            
            
            
            
            
            
            
            
            
            
            
            
            
            

        except openai.error.AuthenticationError:
            logging.error("Invalid API key provided.")
            return JsonResponse({"error": "Invalid API key. Please check your configuration."}, status=401)

        except openai.error.RateLimitError:
            logging.error("Rate limit exceeded.")
            return JsonResponse({"error": "Rate limit exceeded. Please try again later."}, status=429)

        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            return JsonResponse({"error": f"OpenAI API error: {str(e)}"}, status=500)

        except json.JSONDecodeError:
            logging.error("Invalid JSON format in the request.")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

    logging.warning("Invalid request method.")
    return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=405)
