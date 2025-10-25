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

## Edit Queue System - Out-of-Order Edit Problem & Solution

### The Problem: Destructive Sequential Edits

In traditional video editing workflows, edits are applied **sequentially and destructively**:

```
Original Video → [Add Voiceover] → Video_v1 → [Add Text] → Video_v2 → [Trim] → Video_v3
```

**This creates critical problems:**

1. **Out-of-Order Edits Fail**: If a user wants to modify the voiceover timing after adding text overlays, the system would need to:
   - Remove the text overlay layer (impossible - it's "baked in")
   - Modify the voiceover
   - Re-apply the text overlay (but parameters may be wrong for the new duration)

2. **Cascading Failures**: Changing an early edit (like trim timing) invalidates all subsequent edits because:
   - Time offsets shift when you trim earlier in the video
   - Audio sync breaks when video duration changes
   - Text overlays appear at wrong timestamps

3. **No True "Update"**: When a user says "move the voiceover from 0.5s to 2s", a naive system would:
   - Apply a new voiceover at 2s
   - **Keep the old voiceover at 0.5s** (duplicate!)
   - Result: Two voiceovers playing simultaneously

### The Solution: Edit Queue with Regeneration from Source

Our implementation uses an **Edit Queue** architecture that regenerates videos from the original source:

```
Original Video
    ↓
Edit Queue: [Voiceover @ 2s, Text @ 5s, Trim 0-10s]
    ↓
Video Pipeline Service applies ALL edits sequentially from scratch
    ↓
Final Video (clean slate, no cascading issues)
```

**Key Components:**

#### 1. Edit Queue Data Structure (`backend/app/models/edit_models.py`)

```python
@dataclass
class Edit:
    id: str                    # Unique identifier for finding/updating
    type: EditType             # voiceover, text_overlay, trim, filter
    params: dict               # Type-specific parameters
    status: EditStatus         # pending, applied, reverted
    timestamp: str             # When edit was created
    result_video_url: str      # Final video after this edit

@dataclass
class EditQueue:
    session_id: str
    original_video_url: str    # Always start from original
    edits: list[Edit]          # Ordered list of edits
    current_video_url: str     # Latest output
```

#### 2. Video Pipeline Service (`backend/app/services/video_pipeline_service.py`)

**Regenerates the entire video from scratch on every change:**

```python
def apply_edit_queue(edit_queue: EditQueue) -> str:
    """Apply all edits sequentially starting from original video"""
    
    current_video = edit_queue.original_video_url
    
    # Apply each edit in order, starting fresh
    for edit in edit_queue.edits:
        if edit.status == 'applied':
            current_video = apply_single_edit(current_video, edit)
    
    return current_video
```

#### 3. Agent Tools for Queue Management (`backend/app/multi_tool_agent/edit_queue_tools.py`)

**Tools that understand UPDATE vs ADD semantics:**

- `add_voiceover_edit()`: Add new voiceover to queue
- `update_voiceover_timing()`: **Find and modify existing edit** by ID
- `remove_edit()`: Remove edit and regenerate
- `find_voiceover_edit()`: Locate existing edit to update

**The agent is taught to detect user intent:**

```python
# Agent Instructions (simplified)
"""
When user says:
  - "move voiceover to 2s" → UPDATE existing edit (find ID, then update)
  - "add another voiceover at 5s" → ADD new edit
  - "change the voiceover timing" → UPDATE existing edit
  - "also add voiceover" → ADD new edit

WORKFLOW FOR UPDATES:
1. Call find_voiceover_edit() to get edit ID
2. Call update_voiceover_timing(edit_id, new_params)
3. System regenerates video from original with updated queue

WORKFLOW FOR NEW EDITS:
1. Call add_voiceover_edit(params)
2. System adds to queue and regenerates
"""
```

#### 4. Frontend Edit Queue Display (`frontend/components/EditQueue.tsx`)

**Visual timeline showing all applied edits:**

```typescript
<EditQueue editQueue={editQueue} onRemoveEdit={handleRemoveEdit} />
```

Displays:
- Edit type and sequence number
- Human-readable description with timing
- Remove button for each edit
- Updates in real-time as agent applies changes

### How It Solves Out-of-Order Problems

**Scenario: User wants to move voiceover from 0.5s to 2s after adding text overlays**

**Without Edit Queue (FAILS):**
```
Video_v1 (has voiceover at 0.5s) → [Add text] → Video_v2
→ User: "Move voiceover to 2s"
→ Agent adds SECOND voiceover at 2s (duplicate!)
→ Result: Both voiceovers play simultaneously ❌
```

**With Edit Queue (SUCCEEDS):**
```
Edit Queue: [
  {id: "edit-1", type: "voiceover", params: {start_ms: 500, text: "..."}}
  {id: "edit-2", type: "text_overlay", params: {start_ms: 5000, ...}}
]

→ User: "Move voiceover to 2s"
→ Agent: find_voiceover_edit() → returns "edit-1"
→ Agent: update_voiceover_timing("edit-1", {start_ms: 2000})
→ Queue becomes: [
    {id: "edit-1", type: "voiceover", params: {start_ms: 2000, text: "..."}}
    {id: "edit-2", type: "text_overlay", params: {start_ms: 5000, ...}}
  ]
→ Pipeline regenerates from original_video_url with updated queue
→ Result: Clean video with voiceover at 2s and text at 5s ✅
```

### Benefits

1. **True Updates**: Modify any edit at any time without duplicates
2. **Order Independence**: Change early edits without breaking later ones
3. **Reproducible**: Same edit queue + original video = same result
4. **Version Control**: Store entire edit queue to recreate any version
5. **Undo/Redo**: Simply modify queue and regenerate
6. **Transparent**: User sees full edit history in UI

### Tradeoffs

**Pros:**
- ✅ Handles out-of-order edits perfectly
- ✅ No cascading edit failures
- ✅ Clean, predictable outputs
- ✅ Easy to implement undo/redo

**Cons:**
- ❌ Slower than incremental edits (must regenerate full video)
- ❌ Higher compute cost (re-applies all edits each time)
- ❌ Not suitable for real-time editing UIs

**For our use case (AI agent iterations), regeneration is acceptable because:**
- Edit count is typically low (2-5 edits)
- Users expect slight delays when AI processes requests
- Correctness > speed in creative workflows

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
│   ├── agent.py                   # Main AI agent with dynamic instructions
│   ├── add_text.py                # FFmpeg text overlay tool
│   ├── generate_speech_tool.py    # TTS and audio merging
│   ├── edit_queue_tools.py        # Edit queue management tools (add/update/remove)
│   └── session_data.py            # Session state management
├── models/
│   └── edit_models.py             # Edit and EditQueue data structures
├── services/
│   ├── config_service.py          # Feature config loader
│   ├── database_session_service.py # SQLite session storage
│   ├── gcs_artifact_service.py    # Temporary file storage
│   ├── video_export_service.py    # Final video exports
│   └── video_pipeline_service.py  # Edit queue video regeneration pipeline
└── core/
    ├── env_validation.py          # Startup validation
    └── logging_config.py          # Logging setup

frontend/
├── components/
│   ├── EditQueue.tsx              # Visual timeline of applied edits
│   └── ChatWindow.tsx             # Main chat interface with edit queue
└── types.ts                       # TypeScript types for Edit/EditQueue
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
