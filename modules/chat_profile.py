from dataclasses import dataclass, field
import textwrap
from typing import Dict

@dataclass
class ChatProfile:

    profiles: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            "Chat": {
                "name": "Chat",
                "markdown_description": "챗봇과 영어 대화를 진행할 수 있습니다.",
                "icon": "https://emoji.aranja.com/static/emoji-data/img-apple-160/1f4ac.png",
                "system_prompt": textwrap.dedent("""
                Your Name is Emily, You are English Tutor for korean students
                You play a role in enhancing the other person's English conversational skills while conversing in either English or Korean.
                If the other person's English expressions are awkward or incorrect, you can also correct them.
            """),
            },
            "Teacher": {
                "name": "Teacher",
                "markdown_description": "사용자가 등록한 단어 및 회화 정보를 학습하도록 돕습니다.",
                "icon": "https://emoji.aranja.com/static/emoji-data/img-apple-160/1f393.png",
                "system_prompt": textwrap.dedent("""
                "You can present problems or provide feedback using the English conversational expressions registered by the other party, helping them to memorize the English conversational expressions.
            """),
            },
            "Temp": {
                "name": "Temp",
                "markdown_description": "임시",
                "icon": "https://emoji.aranja.com/static/emoji-data/img-apple-160/1f468-200d-1f4bb.png",
                "system_prompt": textwrap.dedent("""
                "Temp Sentence"
            """),
            },
        }
    )

    def get_cl_chat_profiles(self):
        return [
            {
                "name": profile["name"],
                "markdown_description": profile["markdown_description"],
                "icon": profile["icon"],
            }
            for profile in ChatProfile().profiles.values()
        ]

    def get_system_prompt(self, profile_name):
        return ChatProfile().profiles[profile_name]["system_prompt"]
