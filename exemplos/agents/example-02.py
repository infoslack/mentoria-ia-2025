import os

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]


response = client.responses.parse(
    model="gpt-4o-mini",
    input="Daniel e Geanderson vão gravar uma aula na terça-feira.",
    instructions="Extraia informações do evento.",
    text_format=CalendarEvent,
)

event = response.output[0].content[0].parsed
event.name
event.date
event.participants

print(event.model_dump_json(indent=2))
