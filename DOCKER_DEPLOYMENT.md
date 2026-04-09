# Docker Deployment Guide

This guide explains how to containerize and deploy the HVA Feedback Agent to the cloud.

## Prerequisites

- Docker installed locally
- Docker Hub account (for Docker image registry)
- Cloud platform account (Azure Container Instances, AWS, Google Cloud, etc.)

## Building the Docker Image

### Build locally:
```bash
docker build -t hva-feedback-agent:latest .
```

### Tag for Docker Hub:
```bash
docker tag hva-feedback-agent:latest YOUR_DOCKERHUB_USERNAME/hva-feedback-agent:latest
```

## Running Locally

### Using Docker directly:
```bash
docker run -p 5000:5000 \
  -e GOOGLE_API_KEY="your-api-key" \
  -e SECRET_KEY="your-secret-key" \
  hva-feedback-agent:latest
```

### Using Docker Compose:
```bash
# First, create a .env file with your environment variables:
# GOOGLE_API_KEY=your-api-key
# SECRET_KEY=your-secret-key

docker-compose up
```

The app will be accessible at `http://localhost:5000`

## Deploying to Cloud

### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name hva-feedback-agent \
  --image YOUR_DOCKERHUB_USERNAME/hva-feedback-agent:latest \
  --ports 5000 \
  --environment-variables \
    GOOGLE_API_KEY=your-api-key \
    SECRET_KEY=your-secret-key \
  --cpu 1 --memory 2
```

### AWS Elastic Container Service (ECS)
1. Push image to Amazon ECR
2. Create an ECS task definition referencing your image
3. Launch the service

### Google Cloud Run
```bash
gcloud run deploy hva-feedback-agent \
  --image YOUR_DOCKERHUB_USERNAME/hva-feedback-agent:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars GOOGLE_API_KEY=your-api-key,SECRET_KEY=your-secret-key \
  --memory 2Gi \
  --cpu 1
```

### DigitalOcean App Platform
1. Push image to Docker Hub or DigitalOcean Container Registry
2. Connect DigitalOcean to your repository
3. Configure environment variables
4. Deploy

## Environment Variables

Required variables for production:
- `GOOGLE_API_KEY` - Your Google Gemini API key
- `SECRET_KEY` - Flask secret key for session management
- `PORT` - Port to run on (default: 5000)

## Best Practices

1. **Never commit `.env` files** - Use a secrets management service
2. **Use specific version tags** - Instead of `latest`, use version numbers like `v1.0.0`
3. **Monitor logs** - Configure cloud logging to debug issues
4. **Resource limits** - Start with 1-2 GB memory and scale based on demand
5. **Health checks** - The container includes a health check endpoint

## Troubleshooting

### Container won't start
- Check logs: `docker logs container_id`
- Verify environment variables are set
- Ensure API keys are valid

### Application is slow
- Increase memory allocation (try 4GB)
- Check if API quota limits are reached
- Monitor CPU usage

### File upload issues
- Check `MAX_CONTENT_LENGTH` setting in app.py (currently 10MB)
- Ensure temp storage is available in container
