# 🤖 AI Planner Service

A sophisticated AI-powered service for processing and planning Vietnamese text inputs using advanced natural language processing and temporal reasoning. Leverages state-of-the-art transformer models to intelligently parse, normalize, and schedule planning requests.

## ✨ Features

- **Intelligent Text Inference Pipeline**: Processes Vietnamese text through multiple specialized stages
- **FastAPI Backend**: Production-ready RESTful API with health checks and inference endpoints
- **Advanced NLP Processing**: Includes semantic fixing, temporal reasoning, and conflict resolution
- **Modular & Extensible**: Clean separation of concerns with dedicated processors for different tasks
- **Fully Configurable**: Environment-based configuration for model paths, parameters, and input constraints
- **Comprehensive Response Data**: Detailed output including normalized structures, semantic analysis, and scheduling information

## 🏗️ Architecture

The service consists of several key components:

### Core Modules

- **API Layer** (`app/api/`): FastAPI endpoints for health checks and inference
- **Core** (`app/core/`): Configuration management and model loading utilities
- **Pipelines** (`app/pipelines/`): Main inference pipeline orchestration
- **Processors** (`app/processors/`): Specialized processors including:
   - `json_normalizer`: Normalizes raw output to structured JSON
   - `semantic_fixer`: Fixes semantic issues in parsed data
   - `temporal_reasoner`: Handles temporal and scheduling logic
   - `duration_reasoner`: Calculates task durations
   - `scheduler_reasoner`: Manages scheduling conflicts
   - `conflict_reasoner`: Resolves scheduling conflicts
   - `planner_mapper`: Maps data to planner format
   - `response_builder`: Builds final API responses
   - `reply_finalizer`: Finalizes user-facing replies
- **Schemas** (`app/schemas/`): Pydantic models for data validation
- **Model** (`model/`): Pre-trained transformer model files (safetensors format)

## 📋 Prerequisites

- Python 3.10 or higher
- pip or conda for package management
- At least 4GB RAM (8GB+ recommended for model inference)
- CUDA-capable GPU (optional, for faster inference)

## 🚀 Installation & Setup

### Step 1: Clone and Navigate

```bash
cd d:\Mobile Projects\ai-planner\ai-service
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: The first installation may take a few minutes as it downloads the transformer models and dependencies.

## 🎯 Quick Start

### Running the Service

**Start the FastAPI server:**

```bash
python -m app.api.main
```

The server will start on `http://localhost:8000`

**Access the interactive API documentation:**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests

**Test the inference pipeline:**

```bash
python scripts/test_infer.py
```

This will run a sample inference and display the complete output including normalization, semantic analysis, and temporal reasoning results.

## 📖 API Usage

### Health Check Endpoint

```bash
GET /health
```

**Response:**

```json
{
   "status": "healthy",
   "timestamp": "2024-05-12T10:30:00Z"
}
```

### Inference Endpoint

```bash
POST /infer
Content-Type: application/json

{
  "text": "Hôm nay tôi cần hoàn thành báo cáo trong 2 giờ",
  "base_date": "2024-05-12"  // Optional
}
```

**Response:**

```json
{
  "input_text": "Hôm nay tôi cần hoàn thành báo cáo trong 2 giờ",
  "raw_output": "...",
  "normalized_output": {...},
  "normalizer_issues": [],
  "semantic_output": {...},
  "semantic_issues": [],
  "temporal_output": {...},
  "temporal_issues": [],
  "client_response": {...},
  "final_reply": "Báo cáo được lên lịch...",
  "items": [...],
  "conflicts": []
}
```

### Example Requests

**Using cURL:**

```bash
curl -X POST "http://localhost:8000/infer" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hôm nay tôi cần hoàn thành báo cáo trong 2 giờ",
    "base_date": "2024-05-12"
  }'
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/infer",
    json={
        "text": "Hôm nay tôi cần hoàn thành báo cáo trong 2 giờ",
        "base_date": "2024-05-12"
    }
)
print(response.json())
```

## ⚙️ Environment Variables

Create a `.env` file in the project root to customize settings:

```env
# Model Configuration
MODEL_PATH=./model
MODEL_NAME=model.safetensors

# Input Constraints
MAX_INPUT_LENGTH=256

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Processing Settings
DEVICE=cpu  # or 'cuda' for GPU
```

### Default Values

- `MODEL_PATH`: `./model`
- `MAX_INPUT_LENGTH`: `256`
- `API_HOST`: `localhost`
- `API_PORT`: `8000`
- `DEVICE`: `cpu`

## 🗂️ Project Structure

```
ai-service/
├── app/
│   ├── api/
│   │   └── main.py                 # FastAPI application & endpoints
│   ├── core/
│   │   ├── config.py               # Configuration management
│   │   └── model_loader.py         # Model initialization & loading
│   ├── pipelines/
│   │   └── infer_pipeline.py       # Main inference orchestration
│   ├── processors/
│   │   ├── json_normalizer.py      # Output normalization
│   │   ├── semantic_fixer.py       # Semantic error correction
│   │   ├── temporal_reasoner.py    # Temporal logic processing
│   │   ├── duration_reasoner.py    # Duration calculation
│   │   ├── scheduler_reasoner.py   # Scheduling logic
│   │   ├── conflict_reasoner.py    # Conflict resolution
│   │   ├── planner_mapper.py       # Data mapping for planning
│   │   ├── response_builder.py     # Response construction
│   │   └── reply_finalizer.py      # User message finalization
│   └── schemas/
│       └── planner_schemas.py      # Pydantic data models
├── model/
│   ├── model.safetensors           # Pre-trained model weights
│   ├── tokenizer.json              # Tokenizer configuration
│   ├── tokenizer_config.json       # Tokenizer metadata
│   ├── config.json                 # Model configuration
│   └── generation_config.backup.json
├── scripts/
│   └── test_infer.py               # Inference testing script
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔧 Troubleshooting

### Issue: "Module not found" errors

**Solution:**

```bash
# Ensure you're in the project root directory
pip install -r requirements.txt
# If the issue persists, try reinstalling:
pip install --force-reinstall -r requirements.txt
```

### Issue: Model not found

**Solution:**

```bash
# Verify model files exist in the ./model directory
ls -la ./model/
# Check MODEL_PATH environment variable
# Default path is ./model - adjust if needed
```

### Issue: Out of memory errors

**Solution:**

- Reduce `MAX_INPUT_LENGTH` in environment variables
- Switch to CPU if using CUDA:
   ```bash
   set DEVICE=cpu  # Windows
   export DEVICE=cpu  # macOS/Linux
   ```
- Increase available system RAM

### Issue: API Port Already in Use

**Solution:**

```bash
# Change the port via environment variable
set API_PORT=8001  # Windows
export API_PORT=8001  # macOS/Linux

# Or modify the startup command:
python -m app.api.main --port 8001
```

## 📊 Performance Notes

- **First Run**: May be slower as models are loaded and cached
- **Inference Time**: Typically 2-10 seconds depending on input length and hardware
- **Memory Usage**: ~2-4GB for model loading and inference
- **Batch Processing**: Currently processes one request at a time

## 🔍 Debugging

Enable detailed logging by modifying `app/core/config.py` or setting environment variables:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Usage Examples

### Example 1: Simple Planning Request

```python
request_text = "Tôi cần viết báo cáo ngày hôm nay, dự kiến 2 giờ"
# Returns scheduled task with duration and timeline
```

### Example 2: Complex Multi-Task Request

```python
request_text = "Sáng tôi có họp 1 giờ, chiều viết báo cáo 2 giờ, tối review tài liệu"
# Returns multiple tasks with conflict detection and resolution
```

### Example 3: Temporal Reasoning

```python
request_text = "Tôi sẽ làm cái này sau khi hoàn thành dự án hiện tại, ước tính còn 3 ngày"
# Returns tasks with temporal relationships and scheduling
```

## 🚦 Development Status

- ✅ Core pipeline infrastructure
- ✅ Inference processing with multiple stages
- ✅ FastAPI integration
- ✅ Semantic and temporal processing
- ✅ Conflict resolution
- 🔄 Performance optimization
- 🔄 Extended language support

## 📄 License

[Add your license information here]

## 💬 Support

For issues, questions, or suggestions, please create an issue or contact the development team.

---

**Last Updated**: May 2024

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 5000 
```

The service will be available at `http://localhost:5000`

### API Endpoints

- **GET /health**: Health check endpoint
- **POST /infer**: Inference endpoint

#### Inference Request

```json
{
   "text": "Tôi sẽ làm bài tập với Nam ở thư viện lúc 2 giờ và 3 giờ đi làm bài tập ở trường VKU"
}
```

#### Inference Response

```json
{
  "input_text": "Tôi sẽ làm bài tập với Nam ở thư viện lúc 2 giờ và 3 giờ đi làm bài tập ở trường VKU",
  "raw_output": "...",
  "normalized_output": {...},
  "normalizer_issues": [...],
  "semantic_output": {...},
  "semantic_issues": [...],
  "temporal_output": {...},
  "temporal_issues": [...]
}
```

### Testing

Run the test script to see the inference pipeline in action:

```bash
python scripts/test_infer.py
```

## Development

### Project Structure

```
ai-service/
├── app/
│   ├── api/
│   │   └── main.py          # FastAPI application
│   ├── core/
│   │   ├── config.py        # Configuration settings
│   │   └── model_loader.py  # Model loading utilities
│   ├── pipelines/
│   │   └── infer_pipeline.py # Main inference pipeline
│   ├── processors/
│   │   ├── json_normalizer.py
│   │   ├── reply_finalizer.py
│   │   ├── semantic_fixer.py
│   │   └── temporal_reasoner.py
│   └── schemas/
│       └── planner_schemas.py
├── model/                   # Pre-trained model files
├── scripts/
│   └── test_infer.py        # Test script
└── requirements.txt         # Python dependencies
```

### Adding New Processors

1. Create a new processor in `app/processors/`
2. Implement the processing logic
3. Update the inference pipeline in `app/pipelines/infer_pipeline.py`
4. Add corresponding schemas in `app/schemas/`

## Dependencies

- transformers: For NLP model handling
- torch: PyTorch for deep learning
- fastapi: Web framework
- uvicorn: ASGI server
- pydantic: Data validation
- python-dotenv: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Contact

[Add contact information here]
