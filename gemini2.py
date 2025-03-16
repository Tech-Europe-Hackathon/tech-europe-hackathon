import google.generativeai as genai
import pathlib
import os

# Configure Gemini API with your API key
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Define file path for summaries
summaries_file = "summaries.txt"

# Read the entire file as a single string
if os.path.exists(summaries_file):
    with open(summaries_file, "r", encoding="utf-8") as file:
        summaries_text = file.read()
else:
    summaries_text = ""  # Fallback in case the file is missing

# Print for verification
# print("Summaries loaded:")
# print(summaries_text)
# print("\n")

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

def get_document_id(user_query: str) -> list:
    """Determine the most relevant document based on the user query"""
    prompt = f"""
    You are a B2B sales agent. Given the summaries below, select the most relevant product IDs (one or more) for the customer's inquiry.
    - Each document is labeled as **"Document: [filename].pdf"**.
    - Respond **only with the document filenames.pdf**, separated by commas if multiple documents are relevant.
    
    Summaries:
    {summaries_text}

    Customer Inquiry:
    "{user_query}"

    Reply ONLY with the relevant product names.
    """
    response = model.generate_content(prompt)
    # Extract IDs and return as a list
    document_ids = [doc_id.strip() for doc_id in response.text.split(",")]
    return document_ids

def generate_detailed_response(pdf_paths: list, user_query: str) -> str:
    """Generate a response based on multiple PDF contents and user query."""
    try:
        pdf_contents = []

        print(pdf_paths)

        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                pdf_data = pathlib.Path(pdf_path).read_bytes()
                pdf_contents.append({
                    "mime_type": "application/pdf",
                    "data": pdf_data
                })

        if not pdf_contents:
            return "I couldn't find any relevant documents. Would you like to speak with a sales representative?"

        prompt = f"""
        You are a professional B2B sales agent. Provide a concise, detailed response directly addressing the customer's inquiry below, using only relevant information from the attached documents.

        - Speak naturally and informatively, as if addressing a customer in a business conversation.
        - Reference the specific document(s) where the information is sourced.
        - Begin with a brief introduction of the product(s), followed by detailed features and benefits.
        - Include all products from the attached documents unless the customer inquiry specifies otherwise.
        - Identify yourself as an AI sales agent at the start of your response.
        - Adapt the response style to the communication format (e.g., chat or email).
        - If the inquiry is vague, offer a balanced overview of all relevant products.
        - Do not use markdown or special formatting.


        Customer Inquiry:
        "{user_query}"
        """
        response = model.generate_content(contents=pdf_contents + [prompt])

#        response = model.generate_content(
#            contents=[pdf_contents[0]] + [{"mime_type": "text/plain", "data": prompt}]
 #       )
        return response.text.strip()
    except FileNotFoundError:
        return f"I couldn't find detailed information about this product. Would you like to speak with a sales representative?"
    except Exception as e:
        return f"I'm having trouble processing your request due to {str(e)}. Please try again or contact our sales team."

def process_query(user_query: str):
    """Process the user query and print results"""
    print(f"User Query: {user_query}")
    
    try:
        # Step 1: Get relevant document IDs
        document_ids = get_document_id(user_query)
        if len(document_ids) == 1:
            print(f"Relevant Document ID: {document_ids[0]}")
        else:
            print(f"Relevant Document IDs: {document_ids}")
        
        # Step 2: Construct PDF file paths
        pdf_file_paths = [f"documents/{doc_id}" for doc_id in document_ids if os.path.exists(f"documents/{doc_id}")]

        # Step 3: Generate and print response
        if pdf_file_paths:
            response_text = generate_detailed_response(
                pdf_paths=pdf_file_paths,
                user_query=user_query
            )
        else:
            response_text = "Based on your inquiry, I recommend a product. Would you like more detailed information?"
        
        print("\nResponse:")
        print(response_text)
        print("\nReferenced Documents:", document_ids)

    except Exception as e:
        print(f"Error processing request: {e}")
        print("I'm sorry, I encountered an error processing your request. Please try again.")

if __name__ == "__main__":
    # Example usage with test queries
    test_queries = [
        "I'm looking for a valve that can handle high pressure in an industrial setting.",
        "Do you have anything for extreme temperature conditions?",
        "I need a low-pressure valve for a water system."
    ]

    for query in test_queries:
        process_query(query)
        print("-" * 50)  # Separator between queries

    # Optional: Interactive mode
    while True:
        user_input = input("\nEnter your query (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        process_query(user_input)
        print("-" * 50)