# Provider Access POC: Treatment Relationship Extractor

This project is a Proof-of-Concept (POC) that uses the OpenAI API to automatically extract structured treatment relationship data from a large set of FHIR-formatted JSON files. It intelligently processes a folder of JSON records, identifies and validates relationships between patients and clinical providers, and then aggregates the results into a single, clean JSON file.

## 📖 Description

The core of this project is a Python script (`main.py`) that reads multiple JSON files from a `data` directory. It uses a highly specific prompt to instruct an AI model (`gpt-4o-mini`) to act as a Clinical Data Analyst. This allows it to distinguish between actual clinical providers and other entities like insurance payers, and between actionable treatments and administrative data.

The script filters out irrelevant documentation files, processes the valid data sources, and consolidates all unique treatment relationships into a single `consolidated_results.json` file located in the `results` directory. This automates the tedious process of manual data extraction and structuring from complex healthcare records.

## ✨ Features

- **High-Accuracy AI Extraction:** Leverages a sophisticated, role-based prompt with explicit rules and negative constraints to guide the `gpt-4o-mini` model, ensuring high-quality data extraction.
- **Consolidated JSON Output:** Aggregates findings from all source files into a single, clean `consolidated_results.json` file.
- **Advanced File Filtering:** Automatically identifies and skips common FHIR documentation files (like `StructureDefinition`, `ValueSet`, etc.) to improve speed and prevent irrelevant processing.
- **Structured & Nested Format:** Converts unstructured data into a predictable, nested JSON list where each patient has an associated list of provider interactions.
- **Duplicate Removal:** Ensures that the final consolidated output contains only unique patient-provider-treatment relationships.
- **Data Validation:** Uses Pydantic models to ensure the extracted data conforms to the required schema before processing.
- **Secure API Key Handling:** Safely manages the OpenAI API key using a `.env` file.

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

You need to have Python 3 installed. You will also need an API key from OpenAI with access to the `gpt-4o-mini` model.

### Installation

1. **Clone the Repository**

    ```sh
    git clone <your-repository-url>
    cd ProviderAccessPOC
    ```

2. **Set Up a Virtual Environment (Recommended)**

    ```sh
    # For Windows
    python -m venv env
    .\env\Scripts\activate

    # For macOS/Linux
    python3 -m venv env
    source env/bin/activate
    ```

3. **Install Dependencies**

    ```sh
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables**

    Create a `.env` file in the root directory and add your API key:

    ```
    OPENAI_API_KEY="your_actual_api_key_here"
    ```

## 🛠️ Usage

1. **Prepare Your Data**

    - Make sure the `data` folder exists in the root directory.
    - Place all your FHIR JSON files in the `data` folder.

2. **Run the Script**

    ```sh
    python main.py
    ```

3. **Check the Results**

    - The script will create a `results` folder if it doesn't exist.
    - The processed and aggregated output will be in `results/consolidated_results.json`.

## 🏗️ Built With

- [**Python**](https://www.python.org/) – The core programming language.
- [**OpenAI API**](https://openai.com/api/) – For intelligent data extraction.
- [**Pydantic**](https://docs.pydantic.dev/) – For data validation and schema enforcement.
- [**python-dotenv**](https://pypi.org/project/python-dotenv/) – For managing environment variables.
