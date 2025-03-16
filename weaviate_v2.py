import weaviate
from weaviate.classes.init import Auth
import os
import google.generativeai as genai
import pypdf
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple

def setup_weaviate_client() -> weaviate.Client:
    """Connect to Weaviate Cloud instance using environment variables."""
    # Best practice: store your credentials in environment variables
    wcd_url = os.environ["WCD_URL"]
    wcd_api_key = os.environ["WCD_API_KEY"]
    
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=wcd_url,
        auth_credentials=Auth.api_key(wcd_api_key),
    )
    return client

def setup_gemini_model():
    """Set up and return the Gemini model for text generation."""
    with open("ggl_api_key.txt", "r") as f:
        api_key = f.read().strip()
    # Configure your API key
    genai.configure(api_key=api_key)
    # Set up the model
    model = genai.GenerativeModel('gemini-2.0-flash')
    return model

def qa(prompt: str, model) -> str:
    """Generate content using the Gemini model."""
    response = model.generate_content(prompt)
    return response.text

def load_document(file_path: str) -> str:
    """Load and extract text from a PDF document."""
    reader = pypdf.PdfReader(file_path)
    content = ""
    for page in reader.pages:
        content += page.extract_text()
    return content

def create_comprehensive_summary(document_text: str, model) -> str:
    """Create a detailed summary of a document using the Gemini model."""
    prompt = (f"The following document is a product specification. Please make "
             f"a summary of the document. Please make a summary that includes "
             f"all the key features of the product, such that when one wants to "
             f"decide whether the product is suited for ones needs, one can make "
             f"an informed decision based on this summary.\n"
             f"Document: "
             f"{document_text}")
    summary = qa(prompt, model)
    return summary

def create_summary_short(document_text: str, model) -> str:
    """Create a one-line description of a document using the Gemini model."""
    prompt = ("The following document is a product specification. Please create a "
              "one-line description of the product.\n"
             "Document: "
             f"{document_text}")
    summary = qa(prompt, model)
    return summary

def create_weaviate_schema(client: weaviate.Client) -> None:
    """Create Weaviate schema for documents and summaries if it doesn't exist already."""
    # Check if collection exists and create if needed
    try:
        client.collections.get("Document")
        print("Document collection already exists")
    except weaviate.exceptions.WeaviateEntityNotFoundException:
        # Create document collection
        doc_collection = client.collections.create(
            name="Document",
            properties=[
                {
                    "name": "filename",
                    "dataType": ["text"],
                    "description": "The name of the document file"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The full text content of the document",
                    "tokenization": "word",
                    "indexSearchable": True,
                    "indexFilterable": False
                },
                {
                    "name": "comprehensive_summary",
                    "dataType": ["text"],
                    "description": "A detailed summary of the document",
                    "tokenization": "word",
                    "indexSearchable": True,
                    "indexFilterable": False
                },
                {
                    "name": "short_summary",
                    "dataType": ["text"],
                    "description": "A one-line description of the document",
                    "tokenization": "word",
                    "indexSearchable": True,
                    "indexFilterable": False
                }
            ],
            vectorizer_config={
                "text2vec-contextionary": {
                    "vectorizeClassName": False
                }
            }
        )
        print("Created Document collection")

def populate_weaviate(client: weaviate.Client, model) -> None:
    """Process documents, generate summaries, and populate Weaviate."""
    # Create schema if needed
    create_weaviate_schema(client)
    
    # Get the document collection
    doc_collection = client.collections.get("Document")
    
    # Process each document
    for f in os.listdir("documents"):
        if f.endswith(".pdf"):
            file_path = os.path.join("documents", f)
            print(f"Processing {f}...")
            
            # Check if document already exists in Weaviate using the updated filter syntax
            existing_docs = doc_collection.query.fetch_objects(
                limit=1,
                filters=weaviate.classes.query.Filter.by_property("filename").equal(f)
            )
            
            if existing_docs.objects:
                print(f"Document {f} already exists in Weaviate, skipping...")
                continue
                
            # Load document
            document_text = load_document(file_path)
            
            # Generate summaries
            print(f"Generating summaries for {f}...")
            comprehensive_summary = create_comprehensive_summary(document_text, model)
            short_summary = create_summary_short(document_text, model)
            
            # Add to Weaviate
            print(f"Adding {f} to Weaviate...")
            doc_collection.data.insert({
                "filename": f,
                "content": document_text,
                "comprehensive_summary": comprehensive_summary,
                "short_summary": short_summary
            })
            
            # Sleep to avoid rate limiting
            time.sleep(1)
            
    print("Finished populating Weaviate")
def main():
    """Main function to run the entire process."""
    try:
        print("Setting up Weaviate client...")
        client = setup_weaviate_client()
        
        print("Setting up Gemini model...")
        model = setup_gemini_model()
        
        print("Starting document processing and Weaviate population...")
        populate_weaviate(client, model)
        
        print("Process completed successfully!")
    finally:
        # Ensure connection is properly closed to avoid ResourceWarning
        if 'client' in locals():
            client.close()
            print("Weaviate connection closed properly.")

if __name__ == "__main__":
    main()