import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Pydantic models (no changes here)
class TreatmentRelationship(BaseModel):
    patient_name: str = Field(description="The full name of the patient.")
    provider_name: str = Field(description="The name of the healthcare provider or clinic.")
    treatment_description: str = Field(description="A brief description of the treatment or diagnosis.")

class TreatmentRelationships(BaseModel):
    relationships: List[TreatmentRelationship]

# 2. Initialize the OpenAI client using the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file. Please add it.")
client = OpenAI(api_key=api_key)

def extract_treatment_relationships(data: dict) -> dict | None:
    """
    Extracts treatment relationships from a dictionary of data using an LLM.
    """
    prompt_messages = [
        {
            "role": "system",
            "content": """
            You are an expert data extraction assistant. Your task is to extract treatment relationship details
            from the provided JSON data. Your response must be a JSON object that strictly follows this schema:
            {"relationships": [{"patient_name": "...", "provider_name": "...", "treatment_description": "..."}]}
            Do not include any other text, explanations, or markdown formatting.
            """,
        },
        {
            "role": "user",
            "content": f"Extract the treatment relationships from this data:\n\n{json.dumps(data, indent=2)}",
        },
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt_messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        response_content = response.choices[0].message.content
        parsed_json = json.loads(response_content)
        validated_data = TreatmentRelationships(**parsed_json)
        return validated_data.dict()
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Data validation error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def process_provider_access_folder(input_folder: str, output_folder: str):
    """
    Processes JSON files from an input folder, extracts data,
    and saves the results to an output folder.
    """
    # Create the results directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    print(f"Results will be saved in the '{output_folder}' directory.")

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)
            
            try:
                with open(input_path, 'r') as f:
                    data = json.load(f)
                
                print(f"Processing {filename}...")
                relationships_data = extract_treatment_relationships(data)
                
                if relationships_data:
                    # Create the new output filename
                    base_name = os.path.splitext(filename)[0]
                    output_filename = f"{base_name}_result.json"
                    output_path = os.path.join(output_folder, output_filename)
                    
                    # Save the new JSON file
                    with open(output_path, 'w') as f:
                        json.dump(relationships_data, f, indent=2)
                    print(f"  -> Successfully created {output_filename}")

            except json.JSONDecodeError:
                print(f"Could not decode JSON from file: {filename}")
            except Exception as e:
                print(f"An error occurred while processing {filename}: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    input_directory = 'data'
    output_directory = 'results' # Define the output folder name

    # Ensure the input directory exists
    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' not found.")
        print("Please make sure your JSON files are in that folder.")
    else:
        process_provider_access_folder(input_directory, output_directory)
        print("\nProcessing complete.")