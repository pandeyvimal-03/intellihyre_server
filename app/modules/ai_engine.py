import io
import json
from typing import Any, Optional
import pdfplumber
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.application import ParsedResume

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_text_from_pdf(file_content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

async def parse_resume_with_ai(file_content: bytes) -> ParsedResume:
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        # Mocking for development if API key is not set
        return ParsedResume(
            name="John Doe",
            email="john@example.com",
            skills=["Python", "FastAPI"],
            experience=[],
            education=[],
            certifications=[]
        )

    text_content = await extract_text_from_pdf(file_content)

    system_message = """
    You are an expert resume parser. Extract information from the provided resume text and return it in a structured JSON format that strictly adheres to the ParsedResume Pydantic schema.
    The schema is as follows:
    class ParsedResume(BaseModel):
        name: str
        email: str
        phone: Optional[str] = None
        linkedin_url: Optional[str] = None
        github_url: Optional[str] = None
        skills: List[str] = Field(default_factory=list)
        experience: List[Experience] = Field(default_factory=list)
        education: List[Education] = Field(default_factory=list)
        certifications: List[str] = Field(default_factory=list)

    class Experience(BaseModel):
        company: str
        role: str
        years: float

    class Education(BaseModel):
        degree: str
        institution: str
        year: int

    Ensure all fields are correctly extracted. If a field is not found, omit it or use its default value (e.g., empty list for skills, experience, education, certifications).
    For dates, try to extract them in a consistent format (e.g., YYYY-MM or YYYY).
    """

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": text_content}
        ],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return ParsedResume(**data)

async def calculate_match_score(resume_data: ParsedResume, job_description: str) -> float:
    """
    Calculate a match score between a resume and a job description using OpenAI.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        # Mock score if API key is not set
        return 0.0

    prompt = f"""
    You are an expert HR and recruitment analyst. 
    Evaluate how well the following resume matches the job description. 
    Provide a comprehensive match score between 0.0 and 100.0.
    Consider factors like required skills, experience, education, and overall fit.
    
    JOB DESCRIPTION:
    {job_description}
    
    CANDIDATE RESUME:
    {resume_data.model_dump_json(indent=2)}
    
    Return a JSON object with a single key 'score' containing the match score (e.g., {{ "score": 85.5 }}).
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        score = float(data.get("score", 0.0))
        return max(0.0, min(100.0, score)) # Ensure score is between 0 and 100
    except Exception as e:
        print(f"Error calculating match score: {e}")
        return 0.0 # Return 0.0 in case of error

    """
    Generate tailored interview questions based on Job Description and Candidate Resume.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        return [
            "Tell me about your most challenging project.",
            "How do you handle tight deadlines?",
            "What is your experience with the tech stack mentioned in the JD?",
        ]

    prompt = f"""
    You are an expert technical interviewer. 
    Generate 5 behavioral and technical interview questions for a candidate based on:
    
    JOB DESCRIPTION:
    {job_description}
    
    CANDIDATE RESUME:
    {resume_text}
    
    Return the questions as a JSON list of strings.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("questions", [])

async def transcribe_audio(audio_base64: str) -> str:
    """
    Transcribe base64 encoded audio using OpenAI Whisper.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        return "This is a mock transcript of the candidate's answer."

    import base64
    audio_data = base64.b64decode(audio_base64)
    
    # Whisper expects a file-like object with a proper extension
    audio_file = io.BytesIO(audio_data)
    audio_file.name = "answer.webm"
    
    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    
    return transcript.text

async def evaluate_answer(question: str, answer: str) -> dict[str, Any]:
    """
    Evaluate a candidate's answer to a question and return a score and feedback.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        return {"score": 8.0, "feedback": "Good answer."}

    prompt = f"""
    Question: {question}
    Answer: {answer}
    
    Rate this answer from 0.0 to 10.0 based on technical accuracy and clarity.
    Return JSON: {{"score": 8.5, "feedback": "..."}}
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data

async def generate_followup_question(question: str, answer: str) -> Optional[str]:
    """
    Generate a follow-up question based on the candidate's answer.
    Returns None if no follow-up is necessary.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-...":
        # Mock follow-up
        if len(answer.split()) < 10:
            return "Could you elaborate more on that?"
        return None

    prompt = f"""
    You are an expert technical interviewer.
    Original Question: {question}
    Candidate's Answer: {answer}
    
    If the answer is too brief or could be expanded upon with a relevant follow-up, generate a concise follow-up question.
    If the answer is complete and no follow-up is needed, return an empty string or null.
    
    Return JSON: {{"followup": "..." or null}}
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("followup")
