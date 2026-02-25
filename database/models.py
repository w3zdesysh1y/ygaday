from sqlalchemy import Column, Integer, String, Boolean, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Создаем папку для базы данных если её нет
if not os.path.exists('data'):
    os.makedirs('data')

# Подключение к базе данных SQLite
engine = create_engine('sqlite:///data/game.db?check_same_thread=False')
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    points = Column(Integer, nullable=False)
    question_text = Column(String, nullable=False)
    answer = Column(String, nullable=False)

class GameProgress(Base):
    __tablename__ = 'game_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    question_id = Column(Integer)
    status = Column(String)  # ✅ или ❌
    game_session = Column(String)  # UUID игры

async def async_main():
    """Создание таблиц в базе данных"""
    Base.metadata.create_all(engine)
    print("✅ База данных инициализирована")