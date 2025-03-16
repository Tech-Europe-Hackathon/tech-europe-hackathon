from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pathlib
import os

app = Flask(__name__)
CORS(app) 

# Configure Gemini API with your API key
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")
genai.configure(api_key=API_KEY)

# Product summaries - these could be loaded from a database in a production app
document_summaries = {
    "1.1.1": "High-pressure valve for industrial applications.",
    "1.1.2": "Enhanced high-pressure valve with improved sealing.",
    "1.1.3": "High-pressure valve designed for extreme temperatures.",
    "1.2.1": "Low-pressure valve for standard water systems.",
}

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

def get_document_id(user_query: str) -> list:
    """Determine the most relevant document based on the user query"""
    summaries_text = "\n".join([f"{k}: {v}" for k, v in document_summaries.items()])
    prompt = f"""
    You are a B2B sales agent. Given the summaries below, select the most relevant product IDs (one or more) for the customer's inquiry.

    Summaries:
    {summaries_text}

    Customer Inquiry:
    "{user_query}"

    Reply ONLY with the relevant product ID.
    """
    response = model.generate_content(prompt)
    # return response.text.strip()
    # Extract IDs and return as a list
    document_ids = [doc_id.strip() for doc_id in response.text.split(",") if doc_id.strip() in document_summaries]
    return document_ids

def generate_detailed_response(pdf_paths: list, user_query: str) -> str:
    """Generate a response based on multiple PDF contents and user query."""
    try:
        pdf_contents = []

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
        You are a professional B2B sales agent. Provide a concise, detailed answer directly addressing the customer's inquiry below, using information from all attached documents.
        
        - Speak naturally and informatively, as if you were speaking to a customer.
        - Provide a reference to the document(s) where you got the information from.
        - First, introduce the product(s), then provide detailed information about features and benefits.
        - Identify yourself as an AI sales agent at the beginning of your response.
        - Adapt the style of response to the format (email or chat).

        Customer Inquiry:
        "{user_query}"
        """

        # response = model.generate_content(
        #     contents=pdf_contents + [prompt]
        # )
        response = model.generate_content(
            contents=pdf_contents + [{"mime_type": "text/plain", "data": prompt}]
        )
        return response.text.strip()
    except FileNotFoundError:
        return f"I couldn't find detailed information about this product. Would you like to speak with a sales representative?"
    except Exception as e:
        return f"I'm having trouble processing your request. Please try again or contact our sales team."

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests from the frontend"""
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Step 1: Get relevant document ID
        document_ids = get_document_id(user_query)
        if len(document_ids) == 1: print(f"Relevant Document ID: {document_ids[0]}")
        else: print(f"Relevant Document IDs: {document_ids}")
        
        # Step 2: Construct PDF file paths
        pdf_file_paths = [f"documents/{doc_id}.pdf" for doc_id in document_ids if os.path.exists(f"documents/{doc_id}.pdf")]

        if pdf_file_paths:
            # Step 3: Generate a detailed response using multiple PDFs
            response_text = generate_detailed_response(
                pdf_paths=pdf_file_paths, 
                user_query=user_query
            )
        else:
            # Fallback if no PDFs exist
            recommended_products = ", ".join([document_summaries.get(doc_id, "a product") for doc_id in document_ids])
            response_text = f"Based on your inquiry, I recommend {recommended_products}. Would you like more detailed information?"
        
        return jsonify({
            "text": response_text,
            "documentIds": document_ids
        })
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            "text": "I'm sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
