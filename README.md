## AI-Powered Customer Support Agent
### Overview
This project implements an AI-powered customer support agent designed to automatically answer buyer inquiries about products by leveraging technical documentation. The agent uses a multi-step process to provide accurate and detailed responses based on your product documentation database.
### How It Works
The agent processes incoming customer requests through a two-step approach:

1. Document Selection: The agent first analyzes the customer's request and identifies which technical documents contain the relevant information. This selection is based on pre-generated summaries of the documents, allowing for efficient retrieval without processing the entire documentation set for each query.
2. Response Generation: Once the relevant documents are identified, the agent accesses their full content and generates a comprehensive answer tailored to the customer's specific question.

## Running the Backend

To start the backend, you need to run both `emailPolling.py` and `gemini2.py`.

1. **Run `emailPolling.py`** (Handles email polling)
   ```sh
   python emailPolling.py
   ```

2. **Run `gemini2.py`** (Main backend logic)
   ```sh
   python gemini2.py
   ```

Both scripts should be running simultaneously for the backend to function correctly.

