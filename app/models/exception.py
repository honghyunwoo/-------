class MoneyPrinterTurboException(Exception):
    """Base exception for the application."""
    def __init__(self, message="An unexpected error occurred."):
        self.message = message
        super().__init__(self.message)


class VideoProcessingError(MoneyPrinterTurboException):
    """Exception raised for errors in the video processing."""
    pass


class MaterialError(MoneyPrinterTurboException):
    """Exception raised for errors related to material downloading or processing."""
    pass


class LLMError(MoneyPrinterTurboException):
    """Exception raised for errors related to the LLM service."""
    pass


class TTSError(MoneyPrinterTurboException):
    """Exception raised for errors in the Text-to-Speech service."""
    pass


class SubtitleError(MoneyPrinterTurboException):
    """Exception raised for errors in subtitle generation or processing."""
    pass