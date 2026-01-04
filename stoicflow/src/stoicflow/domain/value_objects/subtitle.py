"""Subtitle-related value objects."""

from pydantic import BaseModel, Field


class SubtitleStyle(BaseModel):
    """Subtitle styling configuration."""

    font_family: str = Field(default="NanumGothic", description="Font family")
    font_size: int = Field(default=60, description="Font size in pixels")
    color: str = Field(default="white", description="Text color")
    stroke_color: str = Field(default="black", description="Stroke/outline color")
    stroke_width: int = Field(default=3, description="Stroke width in pixels")
    position: str = Field(
        default="center",
        description="Position: top, center, bottom",
    )
    margin_bottom: int = Field(default=150, description="Margin from bottom in pixels")
    max_width: int = Field(default=900, description="Maximum text width")
    line_spacing: float = Field(default=1.2, description="Line spacing multiplier")


class Subtitle(BaseModel):
    """A single subtitle entry."""

    text: str = Field(description="Subtitle text")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    style: SubtitleStyle = Field(default_factory=SubtitleStyle)

    @property
    def duration(self) -> float:
        """Get subtitle duration."""
        return self.end_time - self.start_time

    def split_into_chunks(self, max_chars: int = 25) -> list["Subtitle"]:
        """Split long subtitle into multiple chunks with adjusted timing."""
        if len(self.text) <= max_chars:
            return [self]

        words = self.text.split()
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > max_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Distribute time evenly
        chunk_duration = self.duration / len(chunks)
        return [
            Subtitle(
                text=chunk,
                start_time=self.start_time + i * chunk_duration,
                end_time=self.start_time + (i + 1) * chunk_duration,
                style=self.style,
            )
            for i, chunk in enumerate(chunks)
        ]
