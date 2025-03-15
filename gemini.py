import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")
model = genai.GenerativeModel("gemini-pro")

document_summaries = {
    "1.1.1": "Summary of hpv 1: High-pressure valve for industrial applications.",
    "1.1.2": "Summary of hpv 2: Enhanced high-pressure valve with improved sealing.",
    "1.1.3": "Summary of hpv 3: High-pressure valve designed for extreme temperatures.",
    "1.2.1": "Summary of lpv 1: Low-pressure valve for standard water systems.",
    # ... add all other summaries
}

def load_full_document(document_id: str) -> str:
    """Loads the full document content from a file."""
    file_path = f"documents/{document_id}.txt"

    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"File for document ID '{document_id}' not found."
    except Exception as e:
        return f"Error reading file for document ID '{document_id}': {e}"

function_description = {
    "name": "load_full_document",
    "description": "Loads the full document content from a file.",
    "parameters": {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the document to load (e.g., '1.1.1').",
            },
        },
        "required": ["document_id"],
    },
}

def sales_agent_response(user_query):
    summaries_text = "\n".join(
        [f"{doc_id}: {summary}" for doc_id, summary in document_summaries.items()]
    )
    prompt = f"You are a B2B sales agent. Here are the product overviews:\n{summaries_text}\n\nCustomer Inquiry: {user_query}\n\nBased on the inquiry and overviews, which product ID is most relevant?"

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(tools=[function_description]),
    )

    if response.candidates and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        function_args = function_call.args

        if function_name == "load_full_document":
            document_id = function_args.get("document_id")
            full_document = load_full_document(document_id)
            sales_prompt = f"You are a B2B sales agent. Customer Inquiry: {user_query}. Product Details: {full_document}. Generate a sales-oriented response."
            sales_response = model.generate_content(sales_prompt)
            return sales_response.text
        else:
            return "Unknown function called."
    else:
        return response.text

# Example usage
user_query = "We need a high-pressure valve for chemical processing that can withstand extreme temperatures."
result = sales_agent_response(user_query)
print(result)

user_query = "Do you have low pressure valves for standard water systems?"
result = sales_agent_response(user_query)
print(result)