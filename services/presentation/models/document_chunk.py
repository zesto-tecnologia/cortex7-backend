from pydantic import BaseModel

from services.presentation.models.presentation_outline_model import SlideOutlineModel


class DocumentChunk(BaseModel):
    heading: str
    content: str
    heading_index: int
    score: float

    def to_slide_outline(self) -> SlideOutlineModel:
        return SlideOutlineModel(content=f"{self.heading}\n{self.content}")
