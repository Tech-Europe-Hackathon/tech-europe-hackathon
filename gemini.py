import google.generativeai as genai
import os

# Configure API key
genai.configure(api_key="AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")

# Get available models to find the correct model name
available_models = genai.list_models()
model_names = [model.name for model in available_models]
print("Available models:", model_names)

# Select an appropriate model that supports function calling
# Note: Model naming might be "models/gemini-1.5-pro" or similar
model_name = "gemini-2.0-flash"  # Use the appropriate model from the list above

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

# Define tool/function
tool = {
    "function_declarations": [{
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
        }
    }]
}

def sales_agent_response(user_query):
    try:
        # Check if the chosen model exists in available models
        model_found = False
        for model in genai.list_models():
            if model_name in model.name:
                print(f"Using model: {model.name}")
                model_found = True
                model_to_use = model.name
                break
                
        if not model_found:
            print(f"Model {model_name} not found. Using default model.")
            # Use the first model that supports generateContent
            for model in genai.list_models():
                if "generateContent" in model.supported_generation_methods:
                    model_to_use = model.name
                    print(f"Selected model: {model_to_use}")
                    break
        
        # Create model instance
        model = genai.GenerativeModel(model_name=model_to_use)
        
        # Create a second model instance with tools for function calling
        # Only use if the model supports tools
        try:
            model_with_tools = genai.GenerativeModel(
                model_name=model_to_use,
                tools=[tool]
            )
        except Exception as e:
            print(f"Error setting up model with tools: {e}")
            print("Falling back to standard model without tools")
            model_with_tools = model
        
        # Prepare summaries text
        summaries_text = "\n".join(
            [f"{doc_id}: {summary}" for doc_id, summary in document_summaries.items()]
        )
        
        # Initial prompt to identify the relevant document
        prompt = f"""You are a B2B sales agent. Here are the product overviews:
{summaries_text}

Customer Inquiry: {user_query}

Based on the inquiry and overviews, which product ID is most relevant? 
If you need to access the full document details, use the load_full_document function with the appropriate document_id."""

        try:
            # Try with tools first
            response = model_with_tools.generate_content(prompt)
            
            # Process the response
            if hasattr(response, 'candidates') and response.candidates:
                # Check for function calls
                for candidate in response.candidates:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_call = part.function_call
                                if function_call.name == "load_full_document":
                                    document_id = function_call.args["document_id"]
                                    full_document = load_full_document(document_id)
                                    
                                    # Generate sales response with the full document
                                    sales_prompt = f"""You are a B2B sales agent. 
Customer Inquiry: {user_query}
Product Details: {full_document}

Generate a sales-oriented response that addresses the customer's needs."""
                                    
                                    sales_response = model.generate_content(sales_prompt)
                                    return sales_response.text
            
            # If no function call was detected or if function calling didn't work
            # Use the direct response or try a simpler approach
            if hasattr(response, 'text'):
                return response.text
            
            # Extract the relevant document ID from the response manually
            response_text = str(response)
            for doc_id in document_summaries.keys():
                if doc_id in response_text:
                    # Found a document ID in the response
                    full_document = load_full_document(doc_id)
                    sales_prompt = f"You are a B2B sales agent. Customer Inquiry: {user_query}. Product Details: {full_document}. Generate a sales-oriented response."
                    sales_response = model.generate_content(sales_prompt)
                    return sales_response.text
            
            # If no document ID was found in the response
            return f"Based on your inquiry about '{user_query}', I recommend checking our product catalog. Would you like more specific information about any of our valve products?"
            
        except Exception as e:
            print(f"Error generating content: {e}")
            # Fallback approach without function calling
            # Identify the best matching document based on keywords
            best_match = None
            if "high-pressure" in user_query.lower() and "extreme temperature" in user_query.lower():
                best_match = "1.1.3"
            elif "high-pressure" in user_query.lower():
                best_match = "1.1.1"
            elif "low-pressure" in user_query.lower() or "water system" in user_query.lower():
                best_match = "1.2.1"
            
            if best_match:
                full_document = load_full_document(best_match)
                sales_prompt = f"You are a B2B sales agent. Customer Inquiry: {user_query}. Product Details: {full_document}. Generate a sales-oriented response."
                try:
                    sales_response = model.generate_content(sales_prompt)
                    return sales_response.text
                except Exception as e:
                    print(f"Error in fallback response: {e}")
            
            return f"I understand you're interested in our valve products. Based on your inquiry about '{user_query}', I'd be happy to connect you with a sales representative who can provide detailed information about our options."
            
    except Exception as e:
        print(f"Unexpected error in sales_agent_response: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again later or contact our sales team directly."

# Example usage
user_query = "We need a high-pressure valve for chemical processing that can withstand extreme temperatures."
print("\nProcessing query:", user_query)
result = sales_agent_response(user_query)
print("\nRESULT:", result)

user_query = "Do you have low pressure valves for standard water systems?"
print("\nProcessing query:", user_query)
result = sales_agent_response(user_query)
print("\nRESULT:", result)