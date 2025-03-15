import os
import google.generativeai as genai
import pypdf

def setup_gemini_model():
    with open("ggl_api_key.txt", "r") as f:
        api_key = f.read().strip()

    # Configure your API key
    genai.configure(api_key=api_key) # Replace with your actual API key

    # Set up the model
    model = genai.GenerativeModel('gemini-2.0-flash')
    return model

def qa(prompt, model):

    # Generate content=
    response = model.generate_content(prompt)
    return response.text

def load_documents():
    docs = {}
    for f in os.listdir("documents"):
        if f.endswith(".pdf"):
            
            content = load_document(docs, f)
            docs[f] = content
            # print the text of the first page
    return docs

def load_document(f):
    reader = pypdf.PdfReader(os.path.join("documents", f))
    content = ""
    for page in reader.pages:
        content += page.extract_text()
    return content
            
def create_summary(document_text, model):
    prompt = (f"The following document is a product specification. Please make" 
             f" a summary of the document. Please make a summary that includes"
             f"all the key features of the product, such that when one wants to"
             f"decide whether the product is suited for ones needs, one can make"
             f"an informed decision based on this summary.\n"
             f"Document: "
             f"{document_text}")
    summary = qa(prompt, model)
    return summary

def create_summary_short(document_text, model):
    prompt = ("The following document is a product specification. Please create a"
              "one-line description of the product.\n"
             "Document: "
             f"{document_text}")
    summary = qa(prompt, model)
    return summary

def make_and_save_summaries(summary_fct, output_file="summaries.txt"):
    model = setup_gemini_model()
    results = ""
    for f in os.listdir("documents"):
        if f.endswith(".pdf"):
            document_text = load_document(f)
            summary = summary_fct(document_text, model)
            results += f"""Document: {f}\n
Summary: {summary}\n\n"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(results)

def make_and_save_summaries_short():
    make_and_save_summaries(create_summary_short, "summaries_short.txt")


if __name__ == "__main__":
    #print(create_summary_short(load_document("D6010-en.pdf"), setup_gemini_model()))
    make_and_save_summaries_short()
