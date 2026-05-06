# Eldritch Inbox
A horror writing prompt generator based on user-submitted images. Takes an uploaded JPEG/PNG/HEIC file and returns a one-sentence writing prompt ("Write a story about...") and a ~300-word story extract guided by optional style parameters (e.g. perspective, tense) and a lightweight RAG based on exemplar authors in various horror subgenres. Optionally, if users provide their email during form submission, they also receive an email copy of the generated text.

This uniquely combines image-to-text and generative writing assistance functionalities with a horror lens, utilising RAG-based generative AI and workflow automation.

Built as the capstone project for the Digital Futures Frontier AI Academy, February 2026.

## How It Works

Users submit an image file and (optionally) their email and customisation preferences via the web interface. Submission acts as a webhook trigger for an n8n workflow that automates the downstream pipeline. The image is passed through a two-agent n8n workflow: an Image Analysis Agent that produces a structured description of the setting, followed by a Writing Agent that generates a one-sentence horror writing prompt and a 300-word prose extract grounded in that description and a subgenre-specific style reference. Both agents use Gemini 2.5-Flash-Lite for multi-modal handling and low cost. The output is displayed on the page and, if an email address is provided, sent to the user's inbox as a formatted HTML email. All submissions are logged to Firestore.

Users can customise their output by selecting a narrative perspective, tense, and horror subgenre before submitting. They can also retrieve their submission history by entering their email address on the history page.
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI (Python), deployed on Google Cloud Run |
| AI Orchestration | n8n |
| AI Models | Gemini 2.5 Flash Lite (image analysis, writing, email formatting) via OpenRouter connection |
| Database | Google Firestore |
| Email | Gmail via n8n Gmail node |
| Containerisation | Docker, Buildpacks |
 
## Project Structure
 
```
eldritch-inbox/
├── app.py               # FastAPI backend — form submission, history, routing
├── requirements.txt
├── Dockerfile
└── database/
    ├── main.py          # Submission database endpoint
    ├── Dockerfile     
    └── requirements.txt        
└── style-references/
    ├── style.py         # Style references endpoint
    ├── Dockerfile       
    └── requirements.txt
└── static/
    ├── favicon.ico      # Favicon page logo
    ├── index.html       # Main submission page
    ├── history.html     # Submission history page
    └── style.css        # Shared stylesheet
```

## Setup
 
### Prerequisites
 
- Python 3.11+
- Docker
- A Google Cloud project with Firestore enabled
- An n8n instance (self-hosted or cloud)
- A Gmail account for outbound email

### Environment Variables
 
Create a `.env` file in the project root with the following:
 
```
N8N_WEBHOOK_URL=your_n8n_webhook_url
EMAIL_SECRET=your_hmac_secret
```

> The `EMAIL_SECRET` must match the secret used in the n8n hashing code node exactly.

### Running Locally
 
```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```
 
The app will be available at `http://localhost:8080`.
 
### Docker
 
```bash
docker build -t eldritch-inbox .
docker run -p 8080:8080 --env-file .env eldritch-inbox
```

### Deploying to Cloud Run

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/eldritch-inbox
gcloud run deploy eldritch-inbox \
  --image gcr.io/YOUR_PROJECT_ID/eldritch-inbox \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars N8N_WEBHOOK_URL=...,EMAIL_SECRET=...
```
> Actual deployment was run via Buildpacks instead of Docker due to module import and .env access errors unresolvable in the project timeframe. The repo Dockerfile is given for transparency.
 
## n8n Workflow
 
The n8n workflow is triggered by a webhook POST from the FastAPI backend and follows this sequence:
 
```
Webhook → Image Analysis Agent → If Setting Image → Writing Agent → Get Timestamp
       → Post to Firestore → Respond to Webhook
       → If Email Given → Hash Email → Email Writing Agent → Send Email
```

The Image Analysis Agent produces a structured description of the uploaded image across five fields (location, atmosphere, details, sensory, anomaly). The Writing Agent receives this description along with the user's customisation preferences and generates the prompt and extract. If the image is not identifiable as a setting, the workflow returns an `invalid_image` status and the writing pipeline is skipped. If users provide their email, the Email Writing Agent creates an HTML-formatted email using a given HTML template, which is sent to users via the Gmail node after the webhook response.

## Privacy
 
User email addresses are never stored in plain text. Before storage, each address is hashed using HMAC-SHA256 with a private secret. This hash is used solely to associate submissions with a user for the history feature.

## Limitations
- Output quality is dependent on image clarity. Very dark or low-resolution images may produce less specific results.
- The system is optimised for setting-based photographs (buildings, landscapes, interiors, outdoor environments). Portraits, abstract images, and screenshots are rejected at the validation stage.
- The writing pipeline is not conversational — each submission is stateless and independent.
- Due to n8n memory limits, image upload sizes are limited to 2.5MB.
- As LLMs lack word-counting capabilities, outputs may vary slightly in size (typically 250-280 words).

## Responsible AI

Eldritch Inbox uses a generative AI model to produce creative writing content. The following considerations apply to its use:
- **Content scope:** The system is designed exclusively for horror fiction writing prompts. The Writing Agent is instructed to produce atmospheric, setting-grounded prose and is not intended for any other purpose.
- **Human oversight:** All model outputs are logged to Firestore and reviewed periodically to monitor for quality drift or unexpected outputs. The system prompt is adjusted if output quality degrades. Users retain full creative control over how, whether, and to what extent they use any generated content.
- **No output validation:** Generated content is not automatically filtered or validated before being shown to the user. Users should apply their own judgement when using outputs as the basis for their writing.
- **Data minimisation:** Email addresses are hashed before storage and are never retained in plain text. No other personally identifiable information is collected. Images submitted through the form (including image metadata) are not stored.
- **Model limitations:** Outputs may occasionally be generic, inconsistent in quality, or insufficiently grounded in the uploaded image, particularly for low-quality or ambiguous photographs. The tool is intended as a creative starting point, not an authoritative or finished piece of writing.
