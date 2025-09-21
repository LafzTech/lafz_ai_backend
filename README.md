# AI-Powered Ride Booking System

A production-ready, multilingual AI ride booking system with voice and chat interfaces supporting English, Tamil, and Malayalam languages.

## 🚀 Features

- **Multilingual Support**: English, Tamil, Malayalam with real-time translation
- **Dual Interface**: Voice calls/messages and text chat
- **AI-Powered**: AWS Bedrock Agent with Claude 3 Haiku for intelligent conversations
- **Speech Processing**: OpenAI Whisper (STT) and Google TTS
- **Location Services**: Google Places Autocomplete for accurate location resolution
- **Session Management**: Redis-based conversation state management
- **Production Ready**: Docker, Nginx, monitoring, and logging

## 🏗️ Architecture

```
Voice/Chat Input → Translation → AI Agent → Location/Booking APIs → Response Translation → Output
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | REST API with async support |
| **Speech-to-Text** | OpenAI Whisper | Voice recognition |
| **Text-to-Speech** | Google Cloud TTS | Voice synthesis |
| **Translation** | Google Cloud Translation | Language support |
| **AI Agent** | AWS Bedrock + Claude 3 Haiku | Conversation intelligence |
| **Location Service** | Google Places API | Address resolution |
| **Session Store** | Redis | Conversation state |
| **Deployment** | Docker + Nginx | Production deployment |

## 📁 Project Structure

```
lafz_ai/
├── app/
│   ├── api/                    # FastAPI endpoints
│   ├── core/                   # Core utilities (logging, exceptions)
│   ├── models/                 # Pydantic schemas
│   ├── services/               # Business logic services
│   │   ├── translation_service.py
│   │   ├── speech_service.py
│   │   ├── bedrock_service.py
│   │   ├── google_services.py
│   │   ├── session_service.py
│   │   └── conversation_service.py
│   └── lambda_functions/       # AWS Lambda functions
├── config/                     # Configuration management
├── deployment/                 # Docker and deployment configs
├── docs/                       # Documentation
├── tests/                      # Test suites
├── main.py                     # FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
└── docker-compose.yml         # Multi-service setup
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis
- Google Cloud Platform account
- AWS account with Bedrock access
- OpenAI API key

### Environment Setup

1. **Clone the repository**
```bash
git clone <your-repo>
cd lafz_ai
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Configure environment variables**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_BEDROCK_AGENT_ID=your-bedrock-agent-id
AWS_BEDROCK_AGENT_ALIAS_ID=your-bedrock-agent-alias-id

# Ride Booking API
RIDE_API_BASE_URL=http://192.168.1.2:8000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Development Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Redis**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

3. **Run the application**
```bash
python main.py
```

### Production Deployment

1. **Using Docker Compose**
```bash
docker-compose up -d
```

2. **Production deployment**
```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

## 📚 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Process text chat messages |
| `/api/voice` | POST | Process voice input |
| `/api/session/{id}` | GET | Get session status |
| `/api/ride/{id}/status` | GET | Get ride status |
| `/api/ride/{id}/cancel` | POST | Cancel ride |
| `/health` | GET | Health check |

## 🎯 Usage Examples

### Chat API
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "I need a ride from Ukkadam to Gandhipuram",
       "language": "en"
     }'
```

### Voice API
```bash
curl -X POST "http://localhost:8000/api/voice" \
     -F "audio_file=@voice_message.mp3" \
     -F "session_id=session_123"
```

## 🔧 Configuration

### AWS Bedrock Agent Setup

1. **Create Bedrock Agent**
```python
from app.services.bedrock_service import BedrockAgentService

bedrock_service = BedrockAgentService()
agent_id = await bedrock_service.create_agent("RideBookingAgent")
```

2. **Deploy Lambda Function**
```bash
# Package and deploy app/lambda_functions/ride_booking_actions.py
# Update AWS_LAMBDA_FUNCTION_ARN in .env
```

3. **Attach Action Group**
```python
action_group_id = await bedrock_service.attach_action_group(
    agent_id,
    "RideBookingActions",
    lambda_arn,
    "s3://bucket/api-schema.yaml"
)
```

### Google Cloud Setup

1. **Enable APIs**
   - Cloud Translation API
   - Text-to-Speech API
   - Places API

2. **Create Service Account**
   - Download JSON key file
   - Set `GOOGLE_APPLICATION_CREDENTIALS` path

### Redis Configuration

For production, configure Redis with:
- Password authentication
- Memory limits
- Persistence settings

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_chat_api.py
```

## 📊 Monitoring

### Health Checks
- Application: `/ping` and `/health`
- Redis: Built-in health checks
- Nginx: `/nginx-health`

### Logging
- Structured logging with timestamps
- Request/response logging
- Error tracking
- Performance metrics

### Metrics (Optional)
- Prometheus metrics collection
- Grafana dashboards
- Alert configuration

## 🔒 Security

- Input validation with Pydantic
- Rate limiting (Nginx)
- CORS configuration
- Security headers
- Non-root container user
- Secrets management via environment variables

## 🌍 Conversation Flow

```
User: "Hello"
Bot: "Hello! I help with auto ride booking. What is your pickup location?"

User: "Ukkadam Coimbatore"
Bot: "Great! Pickup location set to Ukkadam, Coimbatore. What is your drop location?"

User: "Gandhipuram"
Bot: "Perfect! Drop location set to Gandhipuram. Please provide your phone number."

User: "1234567890"
Bot: "Ride request sent successfully! Ride ID: 123456. Driver will call you in 5 minutes."

User: "Driver details"
Bot: "Driver Name: Raja, Phone: 3698521470"
```

## 🚀 Deployment

### Local Development
```bash
docker-compose up
```

### Production
```bash
# Build and deploy
docker-compose -f deployment/docker-compose.prod.yml up -d

# Scale services
docker-compose -f deployment/docker-compose.prod.yml up --scale ai-ride-booking=3 -d
```

### Environment-specific Configs
- `.env` - Development
- `.env.production` - Production
- `docker-compose.yml` - Development
- `deployment/docker-compose.prod.yml` - Production

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run quality checks
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For support and questions:
- Create GitHub issues
- Check documentation at `/docs`
- Review API documentation at `/docs`

## 📈 Performance

- **Response Time**: < 2s for chat, < 5s for voice
- **Throughput**: 100+ concurrent requests
- **Languages**: 3 supported (EN, TA, ML)
- **Availability**: 99.9% uptime target