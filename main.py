from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from qa_engine import answer_question
import base64
from io import BytesIO
from PIL import Image

app = FastAPI()

# Enable CORS for testing and development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64 image, optional

# Response model
class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

# Main API endpoint
@app.post("/api/", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest):
    # If an image is provided, decode it (optional future OCR support)
    if req.image:
        try:
            image_data = base64.b64decode(req.image)
            image = Image.open(BytesIO(image_data))
            # Optional: OCR or image handling logic here
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode image: {e}")

    # Get the answer and relevant links
    answer, links = answer_question(req.question)
    return AnswerResponse(answer=answer, links=links)

# Root route for testing
@app.get("/")
def read_root():
    return {"message": "Virtual TA is running. Use POST /api/ to ask questions."}
