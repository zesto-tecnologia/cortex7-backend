from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from services.presentation.enums.tone import Tone
from services.presentation.enums.verbosity import Verbosity


class GeneratePresentationRequest(BaseModel):
    content: str = Field(..., description="The content for generating the presentation")
    slides_markdown: Optional[List[str]] = Field(
        default=None, description="The markdown for the slides"
    )
    instructions: Optional[str] = Field(
        default=None, description="The instruction for generating the presentation"
    )
    tone: Tone = Field(default=Tone.DEFAULT, description="The tone to use for the text")
    verbosity: Verbosity = Field(
        default=Verbosity.STANDARD, description="How verbose the presentation should be"
    )
    web_search: bool = Field(default=False, description="Whether to enable web search")
    n_slides: int = Field(default=8, description="Number of slides to generate")
    language: str = Field(
        default="English", description="Language for the presentation"
    )
    template: str = Field(
        default="general", description="Template to use for the presentation"
    )
    include_table_of_contents: bool = Field(
        default=False, description="Whether to include a table of contents"
    )
    include_title_slide: bool = Field(
        default=True, description="Whether to include a title slide"
    )
    files: Optional[List[str]] = Field(
        default=None, description="Files to use for the presentation"
    )
    export_as: Literal["pptx", "pdf"] = Field(
        default="pptx", description="Export format"
    )
    trigger_webhook: bool = Field(
        default=False, description="Whether to trigger subscribed webhooks"
    )
