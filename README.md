# DisclosureAI

DisclosureAI is a small Streamlit app that turns a student's own description of AI use into a clear academic disclosure statement. It does not use APIs, accounts, databases, or external language models.

It also offers an optional, in-memory review of text-based assignment PDFs. The review extracts simple structural facts (such as page count, word count, code-like sections, and a references heading) and provides reflection prompts. It is not an AI-writing detector and never claims to determine authorship or AI-use extent from document text.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL printed by Streamlit.

## Test

```powershell
python -m unittest discover -s tests
```

## Deploy to Streamlit Community Cloud

1. Create an empty GitHub repository named `disclosure-ai`.
2. From this folder, run:

   ```powershell
   git init
   git add app.py disclosure.py document_review.py requirements.txt README.md tests .streamlit .gitignore
   git commit -m "Build DisclosureAI"
   git branch -M main
   git remote add origin https://github.com/<your-username>/disclosure-ai.git
   git push -u origin main
   ```

3. Open [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, choose the repository and `main` branch, and set the entry point to `app.py`.
4. Deploy with the default Python runtime (or Python 3.11 if the option is shown). No secrets or configuration are required.

The application is ready for Community Cloud because it needs only `streamlit` and has no system or private configuration requirements.
