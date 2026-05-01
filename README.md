# AI Planner Service

A sophisticated AI-powered service for processing and planning Vietnamese text inputs using advanced natural language processing and temporal reasoning.

## Features

- **Text Inference Pipeline**: Processes Vietnamese text through multiple stages including normalization, semantic fixing, and temporal reasoning
- **FastAPI Backend**: RESTful API with health checks and inference endpoints
- **Transformer Models**: Utilizes state-of-the-art transformer models for text generation and understanding
- **Modular Architecture**: Clean separation of concerns with dedicated processors for different tasks
- **Configurable**: Environment-based configuration for model paths and parameters

## Architecture

The service consists of several key components:

- **API Layer** (`app/api/`): FastAPI endpoints for health checks and inference
- **Core** (`app/core/`): Configuration and model loading utilities
- **Pipelines** (`app/pipelines/`): Main inference pipeline orchestration
- **Processors** (`app/processors/`): Specialized processors for JSON normalization, semantic fixing, temporal reasoning, and reply finalization
- **Schemas** (`app/schemas/`): Pydantic models for data validation
- **Model** (`model/`): Pre-trained AI model files

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd ai-service
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```bash
   export MODEL_PATH="./model"
   export MAX_INPUT_LENGTH="256"
   ```

## Usage

### Running the Service

Start the FastAPI server:

```bash
uvicorn app.api.main:app --reload
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
