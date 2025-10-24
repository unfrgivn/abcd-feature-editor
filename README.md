# Google Prototype - AI Video Editor Agent

An AI-powered video editing platform that uses Google's Gemini models to automatically analyze creative videos and generate recommendations for text overlays (supers) and voiceovers based on brand-specific tone and guidelines.

## Architecture

```
google-prototype/
├── backend/           # FastAPI backend with AI agent
│   └── app/          # Application root
│       ├── api/      # REST API endpoints
│       ├── config/   # Feature configuration (config.json)
│       ├── core/     # Environment validation, logging
│       ├── data/     # SQLite database storage
│       ├── logs/     # Application logs
│       ├── models/   # Pydantic request/response models
│       ├── multi_tool_agent/  # AI agent and video tools
│       ├── services/ # Business logic services
│       └── main.py   # FastAPI application entry
└── frontend/         # React TypeScript frontend
    ├── components/   # React components
    ├── services/     # API client services
    └── App.tsx       # Main application
```

## Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **uv** (Python package manager) - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Google Cloud Project** with:
  - Gemini API access
  - Cloud Storage buckets
  - BigQuery (optional, for analytics)

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd google-prototype
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd backend/app
uv sync
```

#### Configure Environment Variables

Create `backend/app/.env` with the following required variables:

```bash
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-2.0-flash-exp
MODEL_NAME2=gemini-2.0-flash-thinking-exp-01-21  # Optional, for video analysis
GOOGLE_GENAI_USE_VERTEXAI=false

# Google Cloud Project
PROJECT_ID=your_gcp_project_id
GCS_PROJECT_ID=your_gcp_project_id

# Google Cloud Storage Buckets
GCS_SCRATCH_BUCKET=creative-audit-scratch-pad    # For temporary files
GCS_FINAL_BUCKET=creative-audit-scratch-pad    # For exported videos

# Application Configuration
APP_NAME=wpromote-codesprint-2025
DEFAULT_USER_ID=user1
DEFAULT_SESSION_ID=session1
CONFIG_PATH=config/config.json
DATABASE_PATH=data/sessions.db

# BigQuery Configuration (Optional)
ADS_PLATFORM=your_ads_platform
DATASET_NAME=your_dataset_name
TABLE_NAME=your_table_name
```

#### Configure Features

Edit `backend/app/config/config.json` to define your video editing features:

```json
[
  {
    "id": "a_supers",
    "name": "Feature Name",
    "category": "Attract",
    "description": "Feature description for AI agent",
    "detected": false,
    "llmExplanation": "Analysis from video audit",
    "isFixed": false,
    "videoId": "VID-001",
    "videoUrl": "gs://bucket/path/to/video.mp4",
    "primary_brand_color": "#5db1bd",
    "secondary_brand_color": "#313e48",
    "brand_tone": "Professional, empowering, and supportive"
  }
]
```

**Feature Types** (detected by `id` field):
- `a_supers` - Text overlays only
- `a_supers_with_audio` - Text overlays + voiceover
- `a_voice_and_tone` - Brand voice/tone analysis with voiceover

#### Run Backend

```bash
cd backend/app
uv run python main.py
```

Backend runs on `http://localhost:8000`

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment

Create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
```

#### Run Frontend

```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

## Usage

### Starting a Session

1. **Access Frontend**: Navigate to `http://localhost:5173`
2. **Select Feature**: Choose a video feature from the configured list
3. **Get Recommendations**: AI agent analyzes video and suggests edits
4. **Preview Media**: Review generated audio/video previews
5. **Iterate**: Request changes to voiceover copy or text overlays
6. **Export**: Final videos saved to GCS final bucket

### API Endpoints

#### Session Management
- `POST /api/v1/ai-editor-agent/sessions/create` - Create new session
- `GET /api/v1/ai-editor-agent/sessions/list` - List all sessions
- `GET /api/v1/ai-editor-agent/sessions/get?session_id=X` - Get session details
- `DELETE /api/v1/ai-editor-agent/sessions/delete?session_id=X` - Delete session

#### Agent Interaction
- `POST /api/v1/ai-editor-agent/query` - Send query to AI agent
  ```json
  {
    "query": "Add a voiceover that matches our brand tone",
    "feature_id": "a_supers_with_audio"
  }
  ```

#### Export
- `POST /api/v1/ai-editor-agent/export` - Export final video to GCS
  ```json
  {
    "user_id": "user1",
    "feature_id": "a_supers_with_audio"
  }
  ```

## Configuration Guide

### Brand Customization

Each feature in `config.json` supports brand-specific customization:

```json
{
  "brand_tone": "How the brand communicates (friendly, professional, etc.)",
  "primary_brand_color": "#HEX_COLOR",
  "secondary_brand_color": "#HEX_COLOR"
}
```

The AI agent uses these values to:
- Match voiceover copy to brand voice
- Apply brand colors to text overlays
- Ensure consistency across generated content

### Video Sources

Supported video URL formats:
- **Google Cloud Storage**: `gs://bucket-name/path/to/video.mp4`
- **HTTPS URLs**: `https://storage.googleapis.com/bucket/video.mp4`

### Database

SQLite database at `backend/app/data/sessions.db` stores:
- **sessions**: User session metadata
- **session_state**: Agent state (recommendations, URLs)
- **session_versions**: Version history for rollback

## Development

### Backend Commands

```bash
cd backend/app

# Run with auto-reload
uv run python main.py

# Add dependency
uv add package-name

# Update dependencies
uv sync
```

### Frontend Commands

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

### Project Structure

```
backend/app/
├── multi_tool_agent/
│   ├── agent.py              # Main AI agent with dynamic instructions
│   ├── add_text.py           # FFmpeg text overlay tool
│   ├── generate_speech_tool.py  # TTS and audio merging
│   └── session_data.py       # Session state management
├── services/
│   ├── config_service.py     # Feature config loader
│   ├── database_session_service.py  # SQLite session storage
│   ├── gcs_artifact_service.py     # Temporary file storage
│   └── video_export_service.py     # Final video exports
└── core/
    ├── env_validation.py     # Startup validation
    └── logging_config.py     # Logging setup
```

## Troubleshooting

### Backend won't start

1. **Check environment variables**: Ensure all required vars in `.env`
2. **Validate Python version**: Must be 3.12+
3. **Check logs**: `backend/app/logs/app.log`

### Agent not generating recommendations

1. **Verify GOOGLE_API_KEY**: Test with `curl` to Gemini API
2. **Check feature_id**: Must match `id` in `config.json`
3. **Review video URL**: Ensure GCS bucket is accessible

### Video/audio not generating

1. **FFmpeg installed**: Agent requires FFmpeg
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu
   apt-get install ffmpeg
   ```
2. **Check GCS permissions**: Service account needs read/write access
3. **Review scratch bucket**: Verify `GCS_SCRATCH_BUCKET` exists

### Type errors in agent.py

Pre-existing type warnings from Google ADK API are expected and don't affect runtime:
- `LlmRequest` / `LlmResponse` import warnings
- `HarmCategory` literal type mismatches
- These are false positives from the Google SDK

## License

[Your License Here]
