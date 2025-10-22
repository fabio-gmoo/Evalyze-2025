#!/bin/bash

echo "🚀 Starting Evalyze AI Services..."

# Pull required model first
echo "📥 Pulling llama3.2 model..."
docker-compose exec ollama ollama pull llama3.2

# Wait a bit
sleep 5

# Restart AI service
echo "🔄 Restarting AI service..."
docker-compose restart ai-service

echo "✅ Done! Check logs with: docker-compose logs -f ai-service"
