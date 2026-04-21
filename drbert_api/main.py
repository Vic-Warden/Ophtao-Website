from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

# Initialize the API
app = FastAPI(title="DrBERT Embedding API")

# Load DrBERT model from HuggingFace 
model = SentenceTransformer('Dr-BERT/DrBERT-7GB', device='cpu')

# Expected data model for AnythingLLM (OpenAI format)
class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = "drbert"

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest):
    # Ensure input is a list
    texts = [request.input] if isinstance(request.input, str) else request.input
    
    # Generate embeddings
    embeddings = model.encode(texts)
    
    # Format response
    data = []
    for i, emb in enumerate(embeddings):
        data.append({
            "object": "embedding",
            "embedding": emb.tolist(),
            "index": i
        })
        
    return {
        "object": "list",
        "data": data,
        "model": request.model,
        "usage": {"prompt_tokens": 0, "total_tokens": 0} # Simplified usage stats
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)