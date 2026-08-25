from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List

class ModelServingBackend(ABC):
    """
    Abstract base class for all serving backends.
    """
    
    @abstractmethod
    async def load_model(self, base_model: str, adapter_path: str = None, device: str = "cuda", config: dict = None) -> bool:
        """
        Load the base model and (optionally) the PEFT adapter into memory.
        """
        pass

    @abstractmethod
    async def unload_model(self):
        """
        Free GPU memory.
        """
        pass

    @abstractmethod
    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text token-by-token using SSE streaming.
        Uses the chat template of the tokenizer.
        """
        pass

    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate full text in one go.
        """
        pass
