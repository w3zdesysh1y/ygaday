from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import uuid
import random

from system.keyboards import create_inline_keyboard
from database.requests import (
    select_user, 
    create_user, 
    get_all_questions,
    get_question,
    update_game_progress,
    update_user_stats,
    get_game_progress
)

class GameStates(StatesGroup):
    WAITING_FOR_ANSWER = State()

user_router = Router()

# Главное меню
@user_router.message(CommandStart())
async def main_menu(message: Message):
    user = await select_user(message.from_user.id)
    if not user:
        user = await create_user(message.from_user.id, message.from_user.first_name)
    
    buttons = [
        ['🎮 Выбрать игру', 'show_games'],
        ['📊 Статистика', 'show_stats'],
        ['ℹ️ Правила', 'show_rules']
    ]
    
    await message.answer(
        '🎯 Добро пожаловать в игру "Своя игра"!\n'
        'Выберите действие:',
        reply_markup=create_inline_keyboard(buttons, 1)
    )

# Назад в главное меню
@user_router.callback_query(F.data == 'to_mainmenu')
async def back_to_main_menu(callback: CallbackQuery):
    buttons = [
        ['🎮 Выбрать игру', 'show_games'],
        ['📊 Статистика', 'show_stats'],
        ['ℹ️ Правила', 'show_rules']
    ]
    
    await callback.message.edit_text(
        '🎯 Главное меню:\n'
        'Выберите действие:',
        reply_markup=create_inline_keyboard(buttons, 1)
    )

# Показать правила
@user_router.callback_query(F.data == 'show_rules')
async def show_rules(callback: CallbackQuery):
    rules_text = (
        '📚 Правила игры "Своя игра":\n\n'
        '1. Вы выбираете одну из 10 доступных игр\n'
        '2. В каждой игре 20 случайных вопросов\n'
        '3. Вопросы разделены на 5 категорий по стоимости (100-500)\n'
        '4. За правильный ответ вы получаете очки\n'
        '5. За неправильный ответ очки не списываются\n'
        '6. На каждый вопрос можно ответить только один раз\n'
        '7. Игру можно завершить досрочно\n'
        '8. Отвечайте текстом (регистр не важен)'
    )
    
    buttons = [
        ['⏪ В главное меню', 'to_mainmenu']
    ]
    
    await callback.message.edit_text(
        rules_text,
        reply_markup=create_inline_keyboard(buttons, 1)
    )

# Показать статистику
@user_router.callback_query(F.data == 'show_stats')
async def show_stats(callback: CallbackQuery):
    user = await select_user(callback.from_user.id)
    if not user:
        user = await create_user(callback.from_user.id, callback.from_user.first_name)
    
    total_answers = user.correct_answers + user.wrong_answers
    accuracy = (user.correct_answers / total_answers * 100) if total_answers > 0 else 0
    
    stats_text = (
        '📊 Ваша статистика:\n\n'
        f'💰 Общий счёт: {user.score}\n'
        f'✅ Правильных ответов: {user.correct_answers}\n'
        f'❌ Неправильных ответов: {user.wrong_answers}\n'
        f'📈 Точность: {accuracy:.1f}%'
    )
    
    buttons = [
        ['⏪ В главное меню', 'to_mainmenu']
    ]
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=create_inline_keyboard(buttons, 1)
    )

# Показать список игр
@user_router.callback_query(F.data == 'show_games')
async def show_games(callback: CallbackQuery):
    buttons = []
    
    # Создаем 10 кнопок с играми
    for i in range(1, 11):
        buttons.append([f'🎮 Игра #{i}', f'select_game:{i}'])
    
    buttons.append(['⏪ В главное меню', 'to_mainmenu'])
    
    await callback.message.edit_text(
        '🎯 Выберите игру (1-10):\n'
        'В каждой игре 20 случайных вопросов',
        reply_markup=create_inline_keyboard(buttons, 2)
    )

# Выбор конкретной игры
@user_router.callback_query(F.data.startswith('select_game:'))
async def select_game(callback: CallbackQuery, state: FSMContext):
    game_number = int(callback.data.split(':')[1])
    
    # Создаем новую игровую сессию
    game_session = str(uuid.uuid4())
    await state.update_data(
        game_session=game_session, 
        session_score=0,
        game_number=game_number
    )
    
    # Получаем все вопросы из БД
    all_questions = await get_all_questions()
    
    if len(all_questions) < 20:
        await callback.message.edit_text(
            '❌ Недостаточно вопросов в базе. Добавьте вопросы через админ-панель.',
            reply_markup=create_inline_keyboard([['⏪ В главное меню', 'to_mainmenu']])
        )
        return
    
    # Выбираем 20 случайных вопросов
    selected_questions = random.sample(all_questions, 20)
    
    # Сохраняем вопросы
    questions_data = {}
    for q in selected_questions:
        questions_data[q.id] = {
            'points': q.points, 
            'status': str(q.points),
            'question_text': q.question_text,
            'answer': q.answer
        }
    
    await state.update_data(questions=questions_data)
    
    # Показываем игровое поле
    await show_game_board(callback.message, state, edit=True)

# Показать игровое поле
async def show_game_board(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    questions_data = data.get('questions', {})
    session_score = data.get('session_score', 0)
    game_number = data.get('game_number', 1)
    
    if not questions_data:
        buttons = [['⏪ В главное меню', 'to_mainmenu']]
        if edit:
            await message.edit_text(
                '❌ Игровая сессия не найдена',
                reply_markup=create_inline_keyboard(buttons, 1)
            )
        else:
            await message.answer(
                '❌ Игровая сессия не найдена',
                reply_markup=create_inline_keyboard(buttons, 1)
            )
        return
    
    # Группируем вопросы по стоимости
    buttons = []
    points_order = [100, 200, 300, 400, 500]
    
    for points in points_order:
        # Получаем все вопросы этой стоимости
        points_questions = []
        for q_id, q_data in questions_data.items():
            if q_data['points'] == points:
                points_questions.append((q_id, q_data))
        
        # Сортируем для красоты
        points_questions.sort()
        
        # Создаем ряд кнопок
        if points_questions:
            row = []
            for q_id, q_data in points_questions:
                row.append(q_data['status'])
                row.append(f'question:{q_id}')
            buttons.append(row)
    
    buttons.append(['🏁 Завершить игру', 'complete_game'])
    
    text = (
        f'🎮 Игра #{game_number}\n'
        f'💰 Текущий счёт: {session_score}\n\n'
        f'Выберите вопрос:'
    )
    
    if edit:
        await message.edit_text(
            text,
            reply_markup=create_inline_keyboard(buttons, 2)
        )
    else:
        await message.answer(
            text,
            reply_markup=create_inline_keyboard(buttons, 2)
        )

# Вернуться к игре
@user_router.callback_query(F.data == 'back_to_game')
async def back_to_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_game_board(callback.message, state, edit=True)

# Показать вопрос
@user_router.callback_query(F.data.startswith('question:'))
async def show_question(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    try:
        question_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        await callback.message.answer('❌ Ошибка в данных вопроса')
        return
    
    data = await state.get_data()
    questions_data = data.get('questions', {})
    game_session = data.get('game_session')
    
    if not game_session or question_id not in questions_data:
        await callback.message.answer('❌ Ошибка: вопрос не найден')
        return
    
    question_data = questions_data[question_id]
    
    # Проверяем, не отвечали ли уже
    if question_data['status'] in ['✅', '❌']:
        await callback.message.answer('❌ Вы уже отвечали на этот вопрос!')
        return
    
    await state.update_data(current_question_id=question_id)
    await state.set_state(GameStates.WAITING_FOR_ANSWER)
    
    buttons = [
        ['🔙 К игре', 'back_to_game']
    ]
    
    await callback.message.edit_text(
        f'❓ Вопрос за {question_data["points"]} очков:\n\n'
        f'{question_data["question_text"]}\n\n'
        f'📝 Введите ваш ответ:',
        reply_markup=create_inline_keyboard(buttons, 1)
    )

# Проверка ответа
@user_router.message(GameStates.WAITING_FOR_ANSWER)
async def check_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    
    question_id = data.get('current_question_id')
    game_session = data.get('game_session')
    questions_data = data.get('questions', {})
    session_score = data.get('session_score', 0)
    game_number = data.get('game_number', 1)
    
    if not question_id or not game_session or question_id not in questions_data:
        await message.answer('❌ Ошибка игры. Начните заново.')
        await state.clear()
        return
    
    question_data = questions_data[question_id]
    user_answer = message.text.lower().strip()
    correct_answer = question_data['answer'].lower().strip()
    
    is_correct = user_answer == correct_answer
    status = '✅' if is_correct else '❌'
    
    # Обновляем статус вопроса и счёт
    questions_data[question_id]['status'] = status
    if is_correct:
        session_score += question_data['points']
    
    await state.update_data(questions=questions_data, session_score=session_score)
    
    # Сохраняем прогресс
    await update_game_progress(
        message.from_user.id, 
        question_id, 
        status, 
        game_session
    )
    
    # Обновляем статистику пользователя
    await update_user_stats(
        message.from_user.id, 
        question_data['points'] if is_correct else 0, 
        is_correct
    )
    
    # Отправляем результат
    result_text = (
        f"{'✅ ПРАВИЛЬНО! +' + str(question_data['points']) if is_correct else '❌ НЕПРАВИЛЬНО'}\n"
        f'📖 Правильный ответ: {question_data["answer"]}\n'
        f'💰 Текущий счёт: {session_score}'
    )
    
    buttons = [
        ['🔙 К игре', 'back_to_game']
    ]
    
    await message.answer(
        result_text,
        reply_markup=create_inline_keyboard(buttons, 1)
    )
    
    await state.set_state(None)

# Завершить игру
@user_router.callback_query(F.data == 'complete_game')
async def complete_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    session_score = data.get('session_score', 0)
    game_number = data.get('game_number', 1)
    
    await state.clear()
    
    result_text = (
        f'🎮 Игра #{game_number} завершена!\n'
        f'💰 Итоговый счёт: {session_score}\n\n'
        f'Хотите сыграть ещё?'
    )
    
    buttons = [
        ['🎮 Выбрать игру', 'show_games'],
        ['⏪ В главное меню', 'to_mainmenu']
    ]
    
    await callback.message.edit_text(
        result_text,
        reply_markup=create_inline_keyboard(buttons, 1)
    )