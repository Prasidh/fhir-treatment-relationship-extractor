# Treatment Relationship Extractor

This project is a Proof-of-Concept (POC) that uses the OpenAI API to automatically extract structured treatment relationship data from unstructured JSON files. It processes a folder of JSON records, identifies patient names, provider names, and treatment descriptions, and then saves this structured data into new result files.

## 📖 Description

The core of this project is a Python script (`main.py`) that reads multiple JSON files from a `data` directory. For each file, it sends the content to an AI model (specifically `gpt-4o-mini`) to intelligently identify and extract key pieces of information related to patient treatments.

The script then validates the extracted information to ensure it matches a predefined schema and saves the clean, structured data into a `results` directory. This automates the tedious process of manual data extraction and structuring.

## ✨ Features

* [cite_start]**AI-Powered Data Extraction:** Leverages the OpenAI `gpt-4o-mini` model to understand and pull specific data points from JSON content. [cite: 1]
* [cite_start]**Structured Output:** Converts unstructured data into a clean, predictable JSON format. [cite: 1]
* [cite_start]**Data Validation:** Uses Pydantic models to ensure the extracted data is accurate and conforms to the required schema before saving. [cite: 1]
* [cite_start]**Batch Processing:** Automatically processes all `.json` files within a specified input directory (`data`). [cite: 1]
* [cite_start]**Secure API Key Handling:** Safely manages the OpenAI API key using a `.env` file, which is kept out of version control. [cite: 2, 3]

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

You need to have Python 3 installed. You will also need an API key from OpenAI.

### Installation

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd ProviderAccessPOC
    ```

2.  **Set Up a Virtual Environment (Recommended)**
    ```sh
    # For Windows
    python -m venv env
    .\env\Scripts\activate

    # For macOS/Linux
    python3 -m venv env
    source env/bin/activate
    ```

3.  **Install Dependencies**
    The required Python libraries are listed in `requirements.txt`. Install them using pip:
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    * [cite_start]Create a file named `.env` in the root of the project directory. [cite: 3]
    * [cite_start]Add your OpenAI API key to the `.env` file like this: [cite: 3]
        ```
        OPENAI_API_KEY="your_actual_api_key_here"
        ```

## 🛠️ Usage

1.  **Prepare Your Data**
    * Create a folder named `data` in the project's root directory.
    * Place all the JSON files you want to process inside this `data` folder.

2.  **Run the Script**
    Execute the `main.py` script from your terminal:
    ```sh
    python main.py
    ```

3.  **Check the Results**
    * The script will create a `results` folder.
    * Inside `results`, you will find new JSON files named `<original_filename>_result.json`, containing the structured data.

## 🏗️ Built With

* [**Python**](https://www.python.org/) - The core programming language.
* [cite_start][**OpenAI API**](https://openai.com/api/) - For the intelligent data extraction. [cite: 1]
* [cite_start][**Pydantic**](https://docs.pydantic.dev/) - For data validation and schema enforcement. [cite: 1]
* [cite_start][**python-dotenv**](https://pypi.org/project/python-dotenv/) - For managing environment variables. [cite: 1]
