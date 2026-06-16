from dataclasses import dataclass
from datetime import date


@dataclass
class Vacancy:
    title: str
    link: str
    company: str
    date_text: str
    date: date
    is_hot: bool | None = None

    def to_html(self, index: int) -> str:
        hot_icon = "🔥 " if self.is_hot else ""
        return f'{index}. {hot_icon}<a href="{self.link}">{self.title}</a> (<strong>{self.company}</strong>, {self.date_text})'
