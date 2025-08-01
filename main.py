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
    patient_name: str = Field(description="The full name or ID of the patient.")
    provider_name: str = Field(description="The name or ID of the healthcare provider or clinic.")
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
    """Extracts treatment relationships using the final, high-accuracy prompt."""
    
    # ⭐**FINAL PROMPT: Corrected to handle FHIR references**
    prompt_messages = [
        {
            "role": "system",
            "content": """
            You are a highly precise Clinical Data Analyst. Your mission is to extract factual treatment relationships 
            from FHIR JSON data. A 'treatment relationship' connects a patient to a clinical provider for a specific service.

            --- MANDATORY RULES ---
            1.  **IDENTIFY THE PATIENT**: The patient is identified by a `patient.reference` (like "Patient/Patient2") or a full name.
                - If the reference is "Patient/Patient2", extract "Patient2".
                - If a full name is present (e.g., "Johnny Example1"), use that.
                - If no specific patient can be identified, output "Unknown".
                - **NEGATIVE CONSTRAINT**: Never use the generic word "Patient" as the name.

            2.  **IDENTIFY THE PROVIDER**: The provider must be a clinical entity, identified by a `provider.reference` (like "Organization/ProviderOrganization1") or a name.
                - If the reference is "Organization/ProviderOrganization1", extract "ProviderOrganization1".
                - **ALLOWED PROVIDERS**: Specific practitioner names, medical groups, or clinical facilities.
                - **NEGATIVE CONSTRAINT**: Absolutely NO insurance companies, health plans, or financial payers (e.g., "UPMC Health Plan", "BCBS"). These are not providers.
                - **NEGATIVE CONSTRAINT**: Do NOT extract non-clinical entities like a `RelatedPerson`.

            3.  **IDENTIFY THE TREATMENT**: The description must be a real medical service, diagnosis, or procedure.
                - **NEGATIVE CONSTRAINT**: Do NOT extract administrative data (like "Member Number") or generic system definitions.

            Your response MUST be a JSON object following this exact schema, with no additional commentary:
            {"relationships": [{"patient_name": "...", "provider_name": "...", "treatment_description": "..."}]}
            """,
        },
        {
            "role": "user",
            "content": f"Analyze the following FHIR data from file `{source_file}` and extract all valid relationships according to the strict rules provided:\n\n{json.dumps(data, indent=2)}",
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
    """Groups relationships by patient and restructures into a list of patients with their providers."""
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
    """Processes all relevant JSON files, consolidates results, and saves a single output file."""
    os.makedirs(output_folder, exist_ok=True)
    all_extracted_relationships = []
    
    # Add RelatedPerson to the skip list to prevent misidentifying family as providers
    files_to_skip = ("CodeSystem", "StructureDefinition", "ValueSet", "SearchParameter", "ImplementationGuide", "CapabilityStatement", "RelatedPerson")


    for filename in os.listdir(input_folder):
        if filename.startswith(files_to_skip):
            print(f"Skipping documentation/non-clinical file: {filename}")
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