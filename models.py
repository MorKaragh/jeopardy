import uuid
from uuid import UUID

from pydantic import BaseModel


class Question(BaseModel):
    id: UUID
    cost: int
    text: str
    was_asked: bool = False
    answer: str = None


class Topic(BaseModel):
    name: str
    questions: list[Question] = []


class Game(BaseModel):
    room_name: str
    topics: list[Topic] = []

    def find_question_by_id(self, quesion_id: str):
        for topic in self.topics:
            for question in topic.questions:
                if str(question.id) == quesion_id:
                    return question
        return None

class Player(BaseModel):
    name: str
    score: int = 0
