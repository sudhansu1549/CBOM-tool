# Deploy CryptoSight CBOM Dashboard Online

This dashboard needs `tshark`, so the most reliable online deployment option is **Render with Docker**.

## Option 1: Deploy on Render using Docker

### Step 1: Upload this folder to GitHub

Create a new GitHub repository, for example:

```text
cryptosight-cbom-dashboard
```

Upload all files from this folder:

```text
app.py
requirements.txt
Dockerfile
render.yaml
packages.txt
default_crypto_policy.yaml
README.md
```

### Step 2: Deploy on Render

1. Go to https://render.com
2. Sign in
3. Click **New +**
4. Select **Web Service**
5. Connect your GitHub repository
6. Choose:
   - Environment: Docker
   - Branch: main
   - Plan: Starter or higher
7. Click **Create Web Service**

Render will build the Docker image, install tshark, and publish a live URL.

Your app will open at a URL like:

```text
https://cryptosight-cbom.onrender.com
```

## Option 2: Deploy on Streamlit Community Cloud

Streamlit Cloud may work for small PCAPs, but Render is more reliable because this app depends on tshark.

1. Upload the folder to GitHub
2. Go to https://share.streamlit.io
3. Create a new app
4. Select your GitHub repository
5. Main file path:

```text
app.py
```

6. Deploy

The included `packages.txt` asks Streamlit Cloud to install:

```text
tshark
wireshark-common
```

## Important

This is an upload-only PCAP dashboard. Do not upload confidential production PCAPs to public/free hosting unless you understand the privacy and security implications.

For sensitive PCAPs, deploy privately on:

- Render private service
- AWS ECS/Fargate
- Azure Container Apps
- GCP Cloud Run
- Internal Kubernetes
- Offline/local Docker
