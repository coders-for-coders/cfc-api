from pydantic import BaseModel
from typing import List

class Option(BaseModel):
    """Represents a single answer option for a quiz question."""
    id: str
    text: str

class QuestionContent(BaseModel):
    """Contains the content of a quiz question including text, options and correct answer."""
    text: str 
    options: List[Option]
    correct_answer: str

class Question(BaseModel):
    """Represents a complete quiz question with metadata and content."""
    id: str
    category: str
    question: QuestionContent