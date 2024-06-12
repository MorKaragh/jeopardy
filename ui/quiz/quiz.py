from models import Game, Topic, Question
from faker import Faker

fake = Faker()


def make_fake_question(cost):
    return Question(cost=cost,
                    text=fake.text(max_nb_chars=150),
                    answer=fake.text(max_nb_chars=255))


def make_fake_topic():
    return Topic(name=fake.job(),
                 questions=[make_fake_question(i * 100) for i in range(1, 7)])


def make_fake_game(room_name):
    return Game(room_name=room_name,
                topics=[make_fake_topic() for _ in range(0, 6)])
