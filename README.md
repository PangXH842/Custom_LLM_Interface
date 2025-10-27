Project for 2025 GP8000 NTU

## Singapore Housing & Rental Law Chatbot - AI in property rental laws in Singapore

Our chatbot uses a core AI technique called Retrieval-Augmented Generation (RAG). Instead of just relying on a general AI model, it first retrieves highly relevant, accurate facts from our custom-built Knowledge Base on Singapore housing policies. Then, it uses a powerful Large Language Model (LLM) to formulate a natural, conversational answer based only on those trusted facts. This whole process uses Natural Language Processing (NLP) to understand questions and generate human-like replies, ensuring our answers are both smart and reliable.

---

### Usage

1. Run `pip install -r requirements.txt` to install the required packages
2. Store your Huggingface API key into a file named `.env` in the project's root folder:

```
HF_TOKEN = "hf_xxx"             # <= Your Huggingface API key
BASE_URL = "https://router.huggingface.co/v1"
```

3. Run `python proj/app.py` to activate the server
4. Go to `http://127.0.0.1:5001/` to use the chatbot

---

### Notes 

- 250921 
    - The data stored in json files are probably not enough yet, needs more content. 
    - Tried to crawl the official pages (HDB, URA etc) but not successful. 
    - The `scraper.py` files are unused and untested yet. 
    - TODO: 
        - Make the chatbot support markdown format
        - Enable it to process text files 
        - Replace manual knowledge base with official website data
        - Add edit chat session title, edit/delete messages and delete chat functions

- 250922
    - Added functions: process .txt files, delete and rename chat (double click on sidebar)

---

### Gemini tips (250809):

Excellent! That's a fantastic and highly practical group project. Switching to a powerful base model like Mistral is a great starting point.

Building an LLM specialized for a specific domain like Singapore law and housing is a classic and valuable AI problem. You're moving from a general-purpose chatbot to a specialized expert system.

The approach you need is not just about picking a different model, but about how you provide it with the specialized knowledge it doesn't have. A general model like Mistral knows nothing about HDB's Minimum Occupation Period (MOP) or the specifics of a Tenancy Agreement (TA) in Singapore.

There are two primary methods to impart this knowledge. For your project, you will almost certainly want to start with the first one.

---

### Method 1: Retrieval-Augmented Generation (RAG) - The "Open-Book Exam"

This is the **most important and effective approach** for your use case. It's the industry standard for building knowledge-specific applications.

**The Concept:** Instead of the model "remembering" everything, you give it access to a library of relevant documents and teach it to look up the answer before it replies.

Here is the step-by-step roadmap for your project using RAG:

#### **Step 1: Build Your Knowledge Base**
This is your foundation. Gather high-quality, accurate documents.
*   **Official Sources:** Scrape FAQs and guidelines from the **HDB (Housing & Development Board)** and **URA (Urban Redevelopment Authority)** websites.
*   **Legal Documents:** Find PDF versions of the Singapore Statutes, particularly those related to tenancy, property, and contracts. (e.g., from Singapore Statutes Online).
*   **Templates & Guides:** Collect standard Tenancy Agreement templates and explanatory guides from reputable property and law firm websites.

#### **Step 2: Process and "Vectorize" the Data (The "Indexing")**
A computer can't "read" a PDF. You need to convert your documents into a format it can search for meaning.

*   **Chunking:** Break down your large documents into smaller, manageable paragraphs or "chunks." Each chunk should ideally contain a single, coherent piece of information.
*   **Embeddings:** Use an *embedding model* (like `all-MiniLM-L6-v2` from Hugging Face) to convert each text chunk into a list of numbers (a "vector"). These vectors represent the *semantic meaning* of the text. Chunks with similar meanings will have similar vectors.

#### **Step 3: Store in a Vector Database**
You need a special database to store these vectors so you can search them efficiently.
*   **For your project, start with something simple like [ChromaDB](https://www.trychroma.com/) or [FAISS](https://github.com/facebookresearch/faiss).** They can run locally and are perfect for development. (Pinecone and Weaviate are more powerful, cloud-based options).

#### **Step 4: Implement the RAG Flow in Your App**

This is where you modify your Flask `chat()` function.

1.  **User sends a question:** e.g., "How long is the MOP for a BTO flat?"
2.  **Embed the Question:** Your app takes the user's question and uses the same embedding model to turn it into a vector.
3.  **Search the Vector DB:** Your app searches the vector database for the text chunks that have vectors most similar to the question's vector. You'll get back the top 3-5 most relevant chunks of text from your original documents.
4.  **"Augment" the Prompt:** Now, you construct a new, detailed prompt for the Mistral model. This is the crucial step.

    ```python
    # The relevant chunks you retrieved from your database
    retrieved_context = """
    Chunk 1: The Minimum Occupation Period (MOP) is the period of time you are required to physically occupy your flat before you can sell it on the open market. For Build-To-Order (BTO) flats, the MOP is 5 years from the date of key collection.

    Chunk 2: During the MOP, the flat owner and all occupiers must live in the flat. You are not allowed to rent out the entire flat during this period.
    """

    user_question = "How long is the MOP for a BTO flat?"

    # The prompt you send to the LLM
    final_prompt = f"""
    You are an AI assistant specialized in Singapore housing regulations. 
    Using ONLY the context provided below, answer the user's question accurately.
    If the context does not contain the answer, say 'I do not have enough information to answer that question.'

    CONTEXT:
    {retrieved_context}

    QUESTION:
    {user_question}

    ANSWER:
    """
    ```
5.  **Generate the Answer:** The LLM will now generate a precise answer based *only* on the information you provided, drastically reducing the chance of making things up (hallucination).

**Frameworks to Help:** Look into libraries like **[LangChain](https://www.langchain.com/)** or **[LlamaIndex](https://www.llamaindex.ai/)**. They are designed specifically to simplify this entire RAG pipeline.

---

### Method 2: Fine-Tuning - The "Intensive Study"

**The Concept:** You take a base model (like Mistral) and continue its training on a custom dataset of question-answer pairs specific to Singapore law. This actually modifies the model's internal weights.

*   **When to use it:** You do this *after* RAG. Fine-tuning is not for teaching the model new facts—it's for teaching it a specific *style*, *format*, or *nuance*. For example, you could fine-tune it to sound more like a Singaporean legal advisor or to always answer in a specific bulleted format.
*   **The Challenge:** You need a very high-quality dataset of hundreds or thousands of example conversations. Creating this dataset is a massive amount of work.
*   **How it's done:** You use techniques like LoRA or QLoRA to efficiently fine-tune the model on your dataset.

### Recommendation for Your Project

1.  **Start with RAG.** This will deliver 90% of the value and is the correct architecture for a fact-based Q&A system. It makes your system verifiable (you know where the answer came from) and easy to update (just add new documents to your database).
2.  **Build a great Knowledge Base.** The quality of your source documents will determine the quality of your answers.
3.  **Implement the RAG pipeline.** Use LangChain or LlamaIndex to accelerate your development.
4.  **Add a Disclaimer.** Crucially, your application **must** state clearly that it is not providing legal advice and is for informational purposes only.
5.  **Consider Fine-Tuning Later.** Only if you have a specific stylistic goal in mind and have the time to build a quality dataset should you explore fine-tuning.

You're working on a very relevant and impressive project. Good luck!
