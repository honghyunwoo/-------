"""LLM Provider interface (port)."""

from abc import ABC, abstractmethod

from stoicflow.domain.entities.script import Script


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers.

    Implementations: ClaudeAdapter, GeminiAdapter, OllamaAdapter
    """

    @abstractmethod
    async def generate_script(
        self,
        topic: str | None = None,
        quote: str | None = None,
        author: str | None = None,
        style: str = "stoic",
    ) -> Script:
        """
        Generate a new script for a short video.

        Args:
            topic: Optional topic to focus on
            quote: Optional specific quote to use
            author: Optional author for the quote
            style: Content style (default: stoic philosophy)

        Returns:
            Generated Script entity
        """
        ...

    @abstractmethod
    async def improve_script(self, script: Script, feedback: str) -> Script:
        """
        Improve an existing script based on feedback.

        Args:
            script: The script to improve
            feedback: Improvement suggestions

        Returns:
            Improved Script entity
        """
        ...

    @abstractmethod
    async def generate_title(self, script: Script) -> str:
        """Generate an optimized YouTube title for the script."""
        ...

    @abstractmethod
    async def generate_description(self, script: Script) -> str:
        """Generate an optimized YouTube description."""
        ...

    @abstractmethod
    async def generate_tags(self, script: Script) -> list[str]:
        """Generate relevant tags for the video."""
        ...
