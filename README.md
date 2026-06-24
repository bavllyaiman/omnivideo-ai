# OmniVideo AI

Production-grade AI Video Editing SaaS Platform.

## Architecture

```
omnivideo-ai/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── agents/   # AI agent orchestration
│   │   ├── workers/  # Celery workers
│   │   ├── core/     # Config, DB, security
│   │   └── utils/    # Utilities
│   └── migrations/   # Alembic migrations
├── frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/      # Pages & routes
│   │   ├── components/  # React components
│   │   └── lib/      # Utilities & API
├── docker/           # Dockerfiles
├── k8s/              # Kubernetes manifests
└── .github/workflows/  # CI/CD pipelines
```

## Tech Stack

- **Frontend:** Next.js 15, TypeScript, TailwindCSS, Shadcn UI, React Query, Zustand
- **Backend:** FastAPI, Python 3.11, PostgreSQL, Redis
- **Workers:** Celery, Redis Queue
- **Storage:** S3-compatible (Cloudflare R2, AWS S3, MinIO)
- **Video Processing:** FFmpeg, OpenCV, MoviePy
- **Auth:** JWT, OAuth (Google, GitHub)
- **Payments:** Stripe
- **Deployment:** Docker, Docker Compose, Kubernetes

## AI Agents

1. **Video Understanding Agent** - Scene detection, object detection, emotion analysis
2. **Speech Recognition Agent** - Transcription, speaker diarization
3. **Translation Agent** - 100+ language translation
4. **Video Editor Agent** - Auto-editing, silence removal, effects
5. **Shorts Generator Agent** - TikTok, Reels, Shorts creation
6. **Subtitle Agent** - Dynamic/animated subtitles
7. **Thumbnail Agent** - AI thumbnail generation
8. **Content Repurposing Agent** - Blog, social media content
9. **Quality Control Agent** - Output verification

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Development

```bash
# Clone and setup
git clone https://github.com/your-repo/omnivideo-ai.git
cd omnivideo-ai

# Copy environment
cp .env.example .env

# Start services
docker-compose up -d

# Install frontend dependencies
cd frontend && npm install

# Run development
npm run dev
```

### Production

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

See `.env.example` for all required environment variables.

## License

Proprietary - All rights reserved.
