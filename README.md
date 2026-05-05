# Eldritch Inbox
A horror writing prompt generator based on user-submitted images. Takes an uploaded JPEG/PNG/HEIC file and returns a one-sentence writing prompt ("Write a story about...") and a ~300-word story extract guided by optional style parameters (e.g. perspective, tense) and a lightweight RAG based on exemplar authors in various horror subgenres. Optionally, if users provide their email during form submission, they also receive an email copy of the generated text.

This uniquely combines image-to-text and generative writing assistance functionalities with a horror lens

Built as the capstone project for the Digital Futures Frontier AI Academy, February 2026.

## How It Works

Users submit an image file and (optionally) their email and customisation preferences into the Cloud Run hosted frontend. The form submission passes through to an n8n webhook which automates the workflow.
