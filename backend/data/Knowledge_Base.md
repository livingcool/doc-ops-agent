The `GOOGLE_API_KEY` environment variable is required to authenticate with the Google AI API.

1.  Go to Google AI Studio.
2.  Log in with your Google account.
3.  Click **"Create API key in new project"** and copy the generated key.

## 6. Running the Project

To deploy the backend to a persistent cloud service like Render, follow these steps:

1.  **Create a New Service**: Navigate to your Render dashboard and click **New +** > **Web Service**.
2.  **Connect Your Repository**: Connect your GitHub repository containing the backend code.
3.  **Configure Your Service**:
    *   **App Name**: Choose a name for your application.
    *   **Region**: Select a region close to your users.
    *   **Branch**: Select the branch you want to deploy (e.g., `main`).
    *   **Root Directory**: Leave this blank unless your `pyproject.toml` is in a subdirectory.
    *   **Build Command**: `npm run build`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
4.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file. You can also add `CONFIDENCE_THRESHOLD` here if you want to override the default.
5.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

### Relevant Code Changes
```diff
diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
index 50f67b4..53fa41d 100644
--- a/backend/USER_GUIDE.md
+++ b/backend/USER_GUIDE.md
@@ -125,9 +125,9 @@ This is a secret phrase you create. It should be a long, random string. You will
 
 #### Google AI API Key (`GOOGLE_API_KEY`)
 
-1.  Log in to your OpenAI Platform account.
-2.  Go to the **API Keys** section.
-3.  Click **Create new secret key**, give it a name, and copy the key.
+1.  Go to Google AI Studio.
+2.  Log in with your Google account.
+3.  Click **"Create API key in new project"** and copy the generated key.
 
 ## 6. Running the Project
 
@@ -207,9 +207,8 @@ To deploy the backend to a persistent cloud service like Render, follow these st
         *   This is usually the default and is correct.
     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
         *   Use the port recommended by Render (e.g., `10000`).
-3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
-4.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file. You can also add `CONFIDENCE_THRESHOLD` here if you want to override the default.
-5.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file. You can also add `CONFIDENCE_THRESHOLD` here if you want to override the default.
+4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
 
 Your agent is now live and will run automatically in the cloud!

```