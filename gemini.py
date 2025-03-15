import google.generativeai as genai
import pathlib

# Gemini API konfigurieren (ersetze mit deinem API-Key)
genai.configure(api_key="AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")

# Produktzusammenfassungen
document_summaries = {
    "1.1.1": "High-pressure valve for industrial applications.",
    "1.1.2": "Enhanced high-pressure valve with improved sealing.",
    "1.1.3": "High-pressure valve designed for extreme temperatures.",
    "1.2.1": "Low-pressure valve for standard water systems.",
}

# Schritt 1: Erhalte relevante Dokument-ID
def get_document_id(user_query: str) -> str:
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

# Schritt 2: PDF-Datei laden und zusammenfassen mit Gemini
def generate_detailed_response(pdf_path: str, user_query: str) -> str:
    try:
        pdf_data = pathlib.Path(pdf_path).read_bytes()

        prompt = f"""
            You are a professional B2B sales agent. Provide a concise, detailed answer directly addressing the customer's inquiry below, focusing exclusively on relevant details. 

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
        return f"PDF file {pdf_path} not found."
    except Exception as e:
        return f"Error processing PDF: {e}"

# Modell-Initialisierung
model = genai.GenerativeModel("gemini-2.0-flash")

# Kundenanfrage
user_query = "We need a high-pressure valve that can withstand extreme temperatures."

# Schritt 1: ID erhalten
document_id = get_document_id(user_query)
print(f"Relevant Document ID: {document_id}")

# Schritt 2: PDF laden
pdf_file_path = pathlib.Path(f"documents/{document_id}.pdf")

# Schritt 3: Zusammenfassung generieren und ausgeben
summary = generate_detailed_response(pdf_path=pdf_file_path, user_query=user_query)
print("Antwort:")
print(summary)
