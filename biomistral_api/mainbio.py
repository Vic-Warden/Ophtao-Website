import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn
import time

# Initialize FastAPI
app = FastAPI(title="BioMistral Clinical API")

# Model configuration
model_id = "ZiweiChen/BioMistral-Clinical-7B"
device = "mps" if torch.backends.mps.is_available() else "cpu"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
).to(device)

# OpenAI-like request structure
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "biomistral"
    max_tokens: int = 256
    temperature: float = 0.1

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    # Get last user message
    user_input = request.messages[-1].content
    
    # Clinical prompt formatting
    prompt = f"### Question:\n{user_input}\n### Answer:\n"
    
    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True if request.temperature > 0 else False
        )
    
    # Decode and extract answer
    full_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    answer = full_text.split("### Answer:")[-1].strip() if "### Answer:" in full_text else full_text

    # Format response
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)