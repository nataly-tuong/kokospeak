from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .catalog import ALL_VOICES
from .script import plan_script

class BlendVoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    voice: str
    weight: float = Field(ge=0, le=100, allow_inf_nan=False)

class VoiceSettings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    language: Literal['a','b','j','z','f','h','i','e','p'] = 'a'
    voice: str = 'af_heart'
    blend: list[BlendVoice] = Field(default_factory=list, max_length=3)
    speed: float = Field(default=1, ge=0.5, le=2, allow_inf_nan=False)
    pitch: float = Field(default=0, ge=-12, le=12, allow_inf_nan=False)  # semitones
    sentencePause: float = Field(default=0.12, ge=0, le=3, allow_inf_nan=False)
    paragraphPause: float = Field(default=0.45, ge=0, le=5, allow_inf_nan=False)
    gain: float = Field(default=0, ge=-12, le=12, allow_inf_nan=False)
    bass: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)
    treble: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)
    effect: Literal['clean','room','radio'] = 'clean'
    trimSilence: bool = True
    normalize: bool = True
    fadeIn: int = Field(default=10, ge=0, le=2000)
    fadeOut: int = Field(default=50, ge=0, le=2000)

    @model_validator(mode='after')
    def voices_match(self):
        available = ALL_VOICES[self.language]
        if self.voice not in available or any(v.voice not in available for v in self.blend):
            raise ValueError('All voices in a blend must belong to the selected language.')
        if self.blend and sum(v.weight for v in self.blend) <= 0:
            raise ValueError('At least one blend weight must be greater than zero.')
        return self

class GenerateRequest(VoiceSettings):
    text: str = Field(min_length=1, max_length=100_000)
    label: str = Field(default='Untitled take', max_length=120)

    @field_validator('text')
    @classmethod
    def clean_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Please enter some text.')
        return value

    @model_validator(mode='after')
    def validate_script(self):
        plan_script(self.text, self.language, self.voice, self.sentencePause, self.paragraphPause)
        return self

class ExportRequest(BaseModel):
    id: UUID
    filename: str = Field(default='koko', max_length=120)
    format: Literal['wav','flac','ogg','mp3'] = 'wav'
