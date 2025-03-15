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

def get_document_id(user_query: str) -> str:
    """Determine the most relevant document based on the user query"""
    summaries_text = "\n".join([f"{k}: {v}" for k, v in document_summaries.items()])
    prompt = f"""
    You are a B2B sales agent. Given the summaries below, select the most relevant product ID for the customer's inquiry.

    Summaries:
    {summaries_text}

    Customer Inquiry:
    "{user_query}"

    Reply ONLY with the relevant product ID.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_detailed_response(pdf_path: str, user_query: str) -> str:
    """Generate a response based on PDF content and user query"""
    try:
        pdf_data = pathlib.Path(pdf_path).read_bytes()

        prompt = f"""
        You are a professional B2B sales agent. Provide a concise, detailed answer directly addressing the customer's inquiry below, focusing exclusively on relevant details.
            Talk naturally and informatively, as if you were speaking to a customer. Give a reference to from where you got the information in the attached file. First start by introducing the product, then provide detailed information about its features and benefits.
            Identify as an ai sales agent at the beginning of your response. Adapt the style of response to the type of format (email or chat).

            Customer Inquiry:
            "{user_query}"
        """

        response = model.generate_content(
            contents=[
                {
                    "mime_type": "application/pdf",
                    "data": pdf_data
                },
                prompt
            ]
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
        document_id = get_document_id(user_query)
        print(f"Relevant Document ID: {document_id}")
        
        # Step 2: Generate response
        pdf_file_path = f"documents/{document_id}.pdf"
        
        # Check if the document exists
        if os.path.exists(pdf_file_path):
            # Generate detailed response from PDF
            response_text = generate_detailed_response(
                pdf_path=pdf_file_path, 
                user_query=user_query
            )
        else:
            # Fallback if PDF doesn't exist
            response_text = f"Based on your inquiry, I recommend our {document_summaries.get(document_id, 'product')}. Would you like more detailed information?"
        
        return jsonify({
            "text": response_text,
            "documentId": document_id
        })
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            "text": "I'm sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
