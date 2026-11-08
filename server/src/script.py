"""Deterministic text planning and explicit script commands."""
from dataclasses import dataclass
import re
import textwrap
from .catalog import ALL_VOICES

@dataclass
class Segment:
    text: str = ''
    voice: str = ''
    pause: float = 0
    gap: float = 0


def plan_script(text: str, language: str, voice: str, sentence_pause: float, paragraph_pause: float):
    segments = []
    buffer = []
    current_voice = voice

    def flush(paragraph: bool):
        if not buffer:
            return
        paragraph_text = ' '.join(buffer)
        buffer.clear()
        sentences = re.split(r'(?<=[.!?])\s+|(?<=[。！？])', paragraph_text)
        for sentence in sentences:
            # Bounded input segments keep long documents responsive to cancellation.
            for piece in textwrap.wrap(sentence, width=350, break_long_words=True, break_on_hyphens=False):
                if piece.strip():
                    segments.append(Segment(piece.strip(), current_voice, gap=sentence_pause))
        if paragraph and segments:
            segments[-1].gap = paragraph_pause

    for line in text.splitlines():
        stripped = line.strip()
        match = re.fullmatch(r'\[(voice|pause)=(.*?)\]', stripped)
        if match:
            flush(False)
            key, value = match.groups()
            if key == 'voice':
                if value not in ALL_VOICES[language]:
                    raise ValueError(f'Voice {value!r} is not available for this language.')
                current_voice = value
            else:
                try:
                    seconds = float(value)
                except ValueError as error:
                    raise ValueError('Pause commands need a number, for example [pause=1.2].') from error
                if not 0 <= seconds <= 10:
                    raise ValueError('Script pauses must be between 0 and 10 seconds.')
                if segments:
                    segments[-1].gap = 0
                segments.append(Segment(pause=seconds))
        elif not stripped:
            flush(True)
        elif stripped.startswith(('[voice=', '[pause=')):
            raise ValueError('Put each [voice=...] or [pause=...] command alone on a line.')
        else:
            buffer.append(stripped)
    flush(False)
    if not any(segment.text for segment in segments):
        raise ValueError('Please enter some spoken text.')
    if segments and segments[-1].text:
        segments[-1].gap = 0
    return segments
