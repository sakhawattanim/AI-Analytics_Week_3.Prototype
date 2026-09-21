# Google Colab Instructions

## 1. Upload and unzip

Upload `business_analytics_lms_colab_simulated.zip` to Colab, then run:

```python
!unzip -q business_analytics_lms_colab_simulated.zip -d /content/lms
%cd /content/lms
```

## 2. Install packages

```python
!pip -q install -r requirements.txt
```

## 3. Start the local web server and create a public temporary link

Run this single Colab cell:

```python
from google.colab.output import eval_js
from threading import Thread
import uvicorn

def run():
    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level="warning")

Thread(target=run, daemon=True).start()
print(eval_js("google.colab.kernel.proxyPort(8000)"))
```

Click the link displayed by the final line. Keep the Colab cell running while you use the site.

## 4. What to test

- Student dashboard and Week 3 module
- Case Conversation: orientation only, not assessed
- Entry Check: first assessed checkpoint
- Admin toggle at top right
- Admin Studio: Practice versus Assessment mode, activity prompts, criteria, feedback, and ladder scripts
- Save Activity: updates `/content/lms/data/course_config.json` for this Colab session

## Important

This is a simulated-chat prototype. It does not call OpenAI, Claude, Perplexity, or any external model. It does not need an API key. Chat decisions use simplified keyword rules, so it is not valid for official grading.

When Colab restarts or disconnects, your server stops. Download `data/course_config.json` if you want to retain admin edits.
