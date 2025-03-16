from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pathlib
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini API with your API key
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Define file path for document summaries
summaries_file = "summaries.txt"

# Read summaries if file exists
if os.path.exists(summaries_file):
    with open(summaries_file, "r", encoding="utf-8") as file:
        summaries_text = file.read()
else:
    summaries_text = ""

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# Maintain chat history
chat_history = []


def get_document_id(user_query: str) -> list:
    """Determine the most relevant document(s) based on the user query."""
    prompt = f"""
    You are a B2B sales agent. Given the summaries below, select the most relevant product IDs (one or more) for the customer's inquiry.
    - Each document is labeled as "Document: [filename].pdf".
    - Respond only with the document filenames.pdf, separated by commas if multiple documents are relevant.

    Summaries:
    {summaries_text}

    Customer Inquiry:
    "{user_query}"

    Reply ONLY with the relevant product names.
    """
    response = model.generate_content(prompt)
    document_ids = [doc_id.strip() for doc_id in response.text.split(",")]
    return document_ids


def generate_detailed_response(pdf_paths: list, user_query: str, history: list) -> str:
    """Generate a response based on multiple PDFs and user query."""
    try:
        pdf_contents = []

        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                pdf_data = pathlib.Path(pdf_path).read_bytes()
                pdf_contents.append({"mime_type": "application/pdf", "data": pdf_data})

        if not pdf_contents:
            return "I couldn't find any relevant documents. Would you like to speak with a sales representative?"

        # Append chat history to prompt
        history_text = "\n".join([f"Customer: {entry['user']}\nAI: {entry['ai']}" for entry in history])

        prompt = f"""
        You are a professional B2B sales agent. Provide a concise, detailed response directly addressing the customer's inquiry below, using only relevant information from the attached documents.

        - Be conversational and introduce yourself once with 'Hi, I am an AI assistant agent'. If you have already introduced yourself, skip this step.
        - Speak naturally, as if you're engaging in an ongoing conversation.
        - Reference the specific document(s) where the information is sourced.
        - Focus on answering the query, avoiding unnecessary introductory statements.
        - If the inquiry is vague, offer a balanced overview of all relevant products.
        - Do not use markdown or special formatting.

        Previous Conversation History:
        {history_text}

        Customer Inquiry:
        "{user_query}"
        """
        response = model.generate_content(contents=pdf_contents + [prompt])

        return response.text.strip()
    except FileNotFoundError:
        return "I couldn't find detailed information about this product. Would you like to speak with a sales representative?"
    except Exception as e:
        return f"I'm having trouble processing your request due to {str(e)}. Please try again or contact our sales team."


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Flask endpoint to process user queries and return AI responses."""
    try:
        data = request.get_json()
        user_query = data.get("query")

        if not user_query:
            return jsonify({"error": "Missing query parameter"}), 400

        # Step 1: Get relevant document IDs
        document_ids = get_document_id(user_query)

        # Step 2: Construct PDF file paths
        pdf_file_paths = [f"documents/{doc_id}" for doc_id in document_ids if os.path.exists(f"documents/{doc_id}")]

        # Step 3: Generate response
        if pdf_file_paths:
            response_text = generate_detailed_response(
                pdf_paths=pdf_file_paths, user_query=user_query, history=chat_history
            )
        else:
            response_text = "Based on your inquiry, I recommend a product. Would you like more detailed information?"

        # Save chat history
        chat_history.append({"user": user_query, "ai": response_text})

        return jsonify({"response": response_text, "referenced_documents": document_ids})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
