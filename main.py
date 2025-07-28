import os
import json
import time
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Pydantic Models ---
class ExtractedRelationship(BaseModel):
    patient_name: str = Field(description="The full name of the patient.")
    provider_name: str = Field(description="The name of the healthcare provider or clinic.")
    treatment_description: str = Field(description="A brief description of the treatment or diagnosis.")
    source: str

class ExtractedRelationships(BaseModel):
    relationships: List[ExtractedRelationship]

# --- OpenAI Client Initialization ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file. Please add it.")
client = OpenAI(api_key=api_key)


# --- Core Functions ---

def extract_treatment_relationships(data: dict, source_file: str) -> List[dict] | None:
    """Extracts treatment relationships using the new high-accuracy prompt."""
    
    # ⭐**NEW: High-Accuracy Prompt**
    prompt_messages = [
        {
            "role": "system",
            "content": """
            You are a meticulous Clinical Data Analyst. Your mission is to extract factual treatment relationships 
            from FHIR JSON data with extreme precision. A 'treatment relationship' is defined as a specific clinical 
            service, diagnosis, or procedure provided to a specific patient by a specific healthcare provider or organization.

            --- MANDATORY RULES ---
            1.  **PATIENT MUST BE A PERSON**: The patient's name must be a person (e.g., "John Smith", "Jane Doe").
                - If no specific person is named as the patient, you MUST output "Unknown".
                - **NEGATIVE CONSTRAINT**: NEVER use generic terms like "Patient" as a name.

            2.  **PROVIDER MUST BE CLINICAL**: The provider must be a clinical entity that directly provides care.
                - **ALLOWED**: Specific practitioner names (e.g., "Dr. Jack Brown"), medical groups (e.g., "Orange Medical Group"), or clinical facilities (e.g., "General Hospital").
                - **NEGATIVE CONSTRAINT**: NEVER extract insurance companies, health plans, or payers (e.g., "UPMC Health Plan", "BCBS"). These are financial entities, not providers.
                - **NEGATIVE CONSTRAINT**: NEVER extract non-clinical persons (e.g., a "RelatedPerson" like a spouse or parent).

            3.  **TREATMENT MUST BE ACTIONABLE**: The description must be a real medical service, diagnosis, procedure, or prescription.
                - **ALLOWED**: "Annual Check-up", "Orthostatic hypotension", "Prescribed Amoxicillin", "Measurement of Cardiac Sampling".
                - **NEGATIVE CONSTRAINT**: NEVER extract administrative details (e.g., "Member Number"), system capabilities, or generic definitions (e.g., "ExplanationOfBenefit references...").

            --- EXAMPLES ---
            - GOOD: {"patient_name": "Johnny Example1", "provider_name": "Practitioner Jack Brown", "treatment_description": "Non-ST elevation (NSTEMI) myocardial infarction"}
            - BAD (Provider is a payer): {"patient_name": "Johnny Example1", "provider_name": "UPMC Health Plan", "treatment_description": "MEDICARE HMO PLAN"}
            - BAD (Treatment is administrative): {"patient_name": "Member 01 Test", "provider_name": "UPMC Health Plan", "treatment_description": "Member Number"}

            Now, analyze the following FHIR data and extract all valid relationships according to these strict rules.
            Your response MUST be a JSON object following this exact schema:
            {"relationships": [{"patient_name": "...", "provider_name": "...", "treatment_description": "..."}]}
            """,
        },
        {
            "role": "user",
            "content": f"FHIR data from file `{source_file}`:\n\n{json.dumps(data, indent=2)}",
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
        
        for rel in parsed_json.get("relationships", []):
            rel['source'] = source_file
            
        validated_data = ExtractedRelationships(**parsed_json)
        return validated_data.model_dump().get("relationships", [])
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Data validation error in {source_file}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while processing {source_file}: {e}")
        return None

def process_and_restructure_data(all_relationships: List[dict]) -> List[dict]:
    """Groups relationships by patient and restructures the data into a list of patients, each with a list of their providers, removing identical relationships."""
    patients_map: Dict[str, List[Dict]] = {}
    seen_relationships = set()

    for rel in all_relationships:
        rel_key = (
            rel.get("patient_name"),
            rel.get("provider_name"),
            rel.get("treatment_description"),
            rel.get("source")
        )
        if rel_key in seen_relationships:
            continue
        
        patient_name = rel["patient_name"]
        
        if patient_name not in patients_map:
            patients_map[patient_name] = []

        patients_map[patient_name].append({
            "provider_name": rel["provider_name"],
            "type": rel["treatment_description"],
            "source": rel["source"]
        })
        
        seen_relationships.add(rel_key)

    final_list = [
        {"patient_name": name, "providers": providers}
        for name, providers in patients_map.items()
    ]
    
    return final_list

def process_provider_access_folder(input_folder: str, output_folder: str):
    """Processes all relevant JSON files, consolidates the results, and saves a single output file."""
    os.makedirs(output_folder, exist_ok=True)
    all_extracted_relationships = []
    
    files_to_skip = ("CodeSystem", "StructureDefinition", "ValueSet", "SearchParameter", "ImplementationGuide", "CapabilityStatement")

    for filename in os.listdir(input_folder):
        if filename.startswith(files_to_skip):
            print(f"Skipping documentation file: {filename}")
            continue

        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"Processing {filename}...")
                relationships = extract_treatment_relationships(data, filename)
                
                if relationships:
                    all_extracted_relationships.extend(relationships)

                time.sleep(1) 

            except json.JSONDecodeError:
                print(f"Could not decode JSON from file: {filename}")
            except Exception as e:
                print(f"An error occurred with {filename}: {e}")

    print("\nConsolidating results...")
    final_output = process_and_restructure_data(all_extracted_relationships)
    
    output_path = os.path.join(output_folder, "consolidated_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)
    print(f"Successfully created consolidated_results.json in the '{output_folder}' directory.")


# --- Main Execution ---
if __name__ == "__main__":
    input_directory = 'data'
    output_directory = 'results'

    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' not found.")
    else:
        process_provider_access_folder(input_directory, output_directory)
        print("\nProcessing complete.")