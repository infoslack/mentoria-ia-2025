from typing import List
from openai import OpenAI
from app.models.embeddings import Document
from app.config.settings import Settings
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.openai_model
        self.default_temperature = settings.openai_temperature
        self.default_max_output_tokens = settings.openai_max_output_tokens
        self.system_prompt_template = settings.openai_system_prompt

    def generate_response(
        self,
        query: str,
        context_documents: List[Document],
        model: str = None,
        temperature: float = None,
        max_output_tokens: int = None,
    ) -> str:
        model = model or self.default_model
        temperature = (
            temperature if temperature is not None else self.default_temperature
        )
        max_output_tokens = max_output_tokens or self.default_max_output_tokens

        context = "\n\n".join([doc.page_content for doc in context_documents])

        prompt = prompt = self.system_prompt_template.format(
            context=context, query=query
        )

        try:
            response = self.client.responses.create(
                model=model,
                input=prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

            return response.output_text

        except Exception as e:
            logger.error(
                "OpenAI response generation failed",
                extra={"error": str(e), "query": query},
            )
            raise Exception(f"Failed to generate response: {str(e)}")
