# DeskHelp Bot - AI-Powered Voice Support System

A real-time voice-enabled IT help desk assistant built with LiveKit, OpenAI, and React. The system provides instant support for common IT issues through natural voice conversations.

## 🎥 Demo Video

Click here to access Demo Video: https://www.loom.com/share/e094cbfaafb443908583656ac679782b?sid=99d674f4-c7b3-4815-81fc-981ef1a20ed4

## 🏗️ Architecture & Implementation

### Backend Stack
- **Framework**: FastAPI for REST API endpoints
- **Agent Framework**: LiveKit Agents for real-time voice processing
- **LLM**: OpenAI GPT-4o-mini for conversation handling
- **STT**: Deepgram Nova-3 for speech-to-text conversion
- **TTS**: Cartesia for text-to-speech synthesis
- **Database**: SQLAlchemy with SQLite for ticket storage
- **Audio Processing**: Silero VAD for voice activity detection

### Frontend Stack
- **Framework**: React 18 with TypeScript
- **UI Library**: Custom CSS with modern design patterns
- **WebRTC**: LiveKit Client SDK for real-time communication
- **Audio Processing**: Web Audio API for microphone input and visualization
- **Build Tool**: Vite for fast development and building

<img width="1215" height="848" alt="Pasted image (8)" src="https://github.com/user-attachments/assets/1118b7c2-ed3b-44c0-9777-9c8396747735" />


## 🚀 Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- uv package manager
- LiveKit Cloud account (or self-hosted LiveKit server)
- API keys for OpenAI, Deepgram, and Cartesia

### Backend Setup

1. **Clone and navigate to the project**:
```bash
git clone https://github.com/lakshya1goel/HelpDesk-Bot
cd deskHelp-bot/backend
```

2. **Install dependencies**:
```bash
uv sync
```

3. **Download required model files**:
```bash
uv run python app/livekit_agent.py download-files
```

4. **Configure environment variables**:
Create `.env.local` file in the backend directory:

```env
# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-livekit-server.com

# Database Configuration
DATABASE_URL=sqlite:///./support_tickets.db

# AI Service API Keys
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key
```

5. **Start the backend services**:
```bash
uv run python app/main.py
```

This starts both the FastAPI server (port 8000) and LiveKit agent.

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd ../frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment** (optional):
Create `.env` file in frontend directory:
```env
VITE_BASE_URL=backend_base_url
```

4. **Start development server**:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 🔮 Future Enhancements

### Planned Features
1. **Location Validation** - Implement address validation and geocoding for accurate customer location data
2. **Initial Time Optimization** - Reduce start delays through model caching and pre-loading strategies
3. **Rate Limits Handling** - Implement a queue mechanism with priority-based request handling for managing rate limits of OpenAI, Cartesia, and Deepgram providers.
4. **Duplicate Issue Prevention** - Check for existing tickets by email to prevent duplicate issue creation
5. **Ticket Resolution Workflow** - Add functionality to mark tickets as resolved with customer confirmation

---
