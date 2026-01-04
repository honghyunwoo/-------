"""Script entity for stoic philosophy shorts."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ScriptStatus(str, Enum):
    """Script processing status."""

    DRAFT = "draft"
    READY = "ready"  # Ready for recording
    RECORDED = "recorded"  # Voice recorded
    COMPOSED = "composed"  # Video composed
    PUBLISHED = "published"


class ScriptSegment(BaseModel):
    """A segment of the script with timing information."""

    type: str = Field(description="Segment type: hook, quote, explanation, cta")
    text: str = Field(description="The actual text content")
    duration_estimate: float = Field(
        default=0.0,
        description="Estimated duration in seconds",
    )
    start_time: float | None = Field(
        default=None,
        description="Start time in final video (set after composition)",
    )
    end_time: float | None = Field(
        default=None,
        description="End time in final video (set after composition)",
    )


class Script(BaseModel):
    """
    A complete script for a Stoic philosophy short.

    Structure follows the proven hook-quote-explanation-cta format.
    """

    id: int = Field(description="Unique script identifier")
    quote: str = Field(description="The main Stoic quote")
    author: str = Field(description="Quote attribution (e.g., Marcus Aurelius)")
    theme: str = Field(default="stoic", description="Content theme")

    # Script segments
    hook: str = Field(description="Opening hook to grab attention (2-3 seconds)")
    quote_read: str = Field(description="Natural reading of the quote")
    explanation: str = Field(description="Modern interpretation/application")
    cta: str = Field(description="Call-to-action ending")

    # Combined text for TTS
    tts_text: str = Field(description="Full text for TTS or recording guide")

    # Metadata
    duration_estimate: float = Field(
        default=45.0,
        description="Estimated total duration in seconds",
    )
    status: ScriptStatus = Field(default=ScriptStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.now)
    used_count: int = Field(default=0, description="How many times this script was used")

    # Audio reference
    audio_path: Path | None = Field(
        default=None,
        description="Path to recorded/generated audio file",
    )

    @property
    def segments(self) -> list[ScriptSegment]:
        """Get script as ordered segments."""
        return [
            ScriptSegment(type="hook", text=self.hook, duration_estimate=3.0),
            ScriptSegment(type="quote", text=self.quote_read, duration_estimate=10.0),
            ScriptSegment(type="explanation", text=self.explanation, duration_estimate=25.0),
            ScriptSegment(type="cta", text=self.cta, duration_estimate=5.0),
        ]

    @property
    def full_text(self) -> str:
        """Get full script text for display."""
        return f"{self.hook}\n\n{self.quote_read}\n\n{self.explanation}\n\n{self.cta}"

    def to_recording_guide(self) -> str:
        """Generate a recording guide for manual voice recording."""
        guide = []
        guide.append("=" * 50)
        guide.append(f"SCRIPT #{self.id} - Recording Guide")
        guide.append(f"Quote: {self.quote[:50]}... - {self.author}")
        guide.append(f"Target Duration: {self.duration_estimate:.0f} seconds")
        guide.append("=" * 50)
        guide.append("")
        guide.append("[HOOK - 2~3 seconds, grab attention]")
        guide.append(f"  {self.hook}")
        guide.append("")
        guide.append("[QUOTE - 8~12 seconds, slow and clear]")
        guide.append(f"  {self.quote_read}")
        guide.append("")
        guide.append("[EXPLANATION - 20~30 seconds, conversational]")
        guide.append(f"  {self.explanation}")
        guide.append("")
        guide.append("[CTA - 3~5 seconds, engaging question]")
        guide.append(f"  {self.cta}")
        guide.append("")
        guide.append("=" * 50)
        guide.append("Tips: Speak naturally, pause between sections")
        guide.append("=" * 50)
        return "\n".join(guide)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Script":
        """Create Script from JSON data (e.g., from scripts_premium.json)."""
        script_data = data.get("script", {})

        # Parse duration_estimate (handle "28초" format)
        duration_raw = data.get("duration_estimate", 45.0)
        if isinstance(duration_raw, str):
            # Extract number from string like "28초"
            import re
            match = re.search(r"(\d+)", duration_raw)
            duration = float(match.group(1)) if match else 45.0
        else:
            duration = float(duration_raw)

        return cls(
            id=data["id"],
            quote=data["quote"],
            author=data["author"],
            theme=data.get("theme", "stoic"),
            hook=script_data["hook"],
            quote_read=script_data["quote_read"],
            explanation=script_data["explanation"],
            cta=script_data["cta"],
            tts_text=data.get("tts_text", ""),
            duration_estimate=duration,
        )
