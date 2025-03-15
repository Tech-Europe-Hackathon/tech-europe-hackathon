import google.generativeai as genai
import subprocess
import os

# API konfigurieren (ersetze durch deinen API-Key)
genai.configure(api_key="AIzaSyDokn1k6Ij48FLTg5bQauestOvumCXM19g")

# Wähle ein geeignetes Modell aus
model = genai.GenerativeModel("gemini-2.0-flash")

# Produktzusammenfassungen
document_summaries = {
    "1.1.1": "High-pressure valve for industrial applications.",
    "1.1.2": "Enhanced high-pressure valve with improved sealing.",
    "1.1.3": "High-pressure valve designed for extreme temperatures.",
    "1.2.1": "Low-pressure valve for standard water systems.",
    # ggf. weitere Zusammenfassungen hinzufügen
}

def generate_response(user_query: str) -> str:
    # Vorbereiten des Prompts
    summaries_text = "\n".join([f"{k}: {v}" for k, v in document_summaries.items()])
    prompt = f"""
    You are a B2B sales agent. Based on the customer's inquiry, choose the most relevant product ID from the provided summaries.

    Summaries:
    {summaries_text}

    Customer Inquiry:
    "{user_query}"

    Reply ONLY with the relevant product ID.
    """

    # Modell-Abfrage
    response = model.generate_content(prompt)
    return response.text.strip()

def load_document(document_id: str):
    pdf_path = f"documents/{document_id}.pdf"

    if os.path.exists(pdf_path):
        # Prüfen ob pdftotext installiert ist
        try:
            subprocess.run(['pdftotext', pdf_path, '-'], check=True)
        except FileNotFoundError:
            print("pdftotext ist nicht installiert. Installiere es mit 'brew install poppler'.")
        except subprocess.CalledProcessError as e:
            print("Fehler beim Lesen des PDFs:", e)
    else:
        print(f"Die Datei {pdf_path} existiert nicht.")


# Beispiel-Anfrage:
user_query = "We need a high-pressure valve that can withstand extreme temperatures."
relevant_document_id = generate_response(user_query)

print("Relevant Document ID:", relevant_document_id)

print("\n--- Dokumentinhalt ---")
load_document(relevant_document_id)
