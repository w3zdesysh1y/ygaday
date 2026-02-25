from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import system_settings
from system.keyboards import create_inline_keyboard
from database.requests import create_question

class AddQuestionStates(StatesGroup):
    WAITING_FOR_POINTS = State()
    WAITING_FOR_QUESTION = State()
    WAITING_FOR_ANSWER = State()

admin_router = Router()

# Проверка на админа
def is_admin(user_id: int) -> bool:
    return str(user_id) == system_settings['mainadmin_id']

@admin_router.message(Command('add_question'))
async def start_add_question(message: Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if not is_admin(message.from_user.id):
        await message.answer('❌ У вас нет прав для выполнения этой команды.')
        return
    
    buttons = [
        ['100', 'points:100'],
        ['200', 'points:200'],
        ['300', 'points:300'],
        ['400', 'points:400'],
        ['500', 'points:500'],
        ['❌ Отмена', 'cancel_add']
    ]
    
    await message.answer(
        'Выберите стоимость вопроса:',
        reply_markup=create_inline_keyboard(buttons, 2)
    )
    await state.set_state(AddQuestionStates.WAITING_FOR_POINTS)

@admin_router.callback_query(F.data.startswith('points:'), AddQuestionStates.WAITING_FOR_POINTS)
async def process_points(callback: CallbackQuery, state: FSMContext):
    points = int(callback.data.split(':')[1])
    await state.update_data(points=points)
    
    await callback.message.edit_text(
        f'✅ Выбрана стоимость: {points} очков\n\n'
        '📝 Теперь введите текст вопроса:'
    )
    await state.set_state(AddQuestionStates.WAITING_FOR_QUESTION)

@admin_router.message(AddQuestionStates.WAITING_FOR_QUESTION)
async def process_question(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text)
    
    buttons = [
        ['❌ Отмена', 'cancel_add']
    ]
    
    await message.answer(
        '📝 Вопрос сохранен.\n\n'
        '✏️ Теперь введите ответ на вопрос:',
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.set_state(AddQuestionStates.WAITING_FOR_ANSWER)

@admin_router.message(AddQuestionStates.WAITING_FOR_ANSWER)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    points = data['points']
    question_text = data['question_text']
    answer = message.text
    
    # Создаем новый вопрос
    question = await create_question(points, question_text, answer)
    
    if question:
        await message.answer(
            '✅ **Вопрос успешно добавлен!**\n\n'
            f'💰 Стоимость: {points}\n'
            f'❓ Вопрос: {question_text}\n'
            f'❗️ Ответ: {answer}'
        )
    else:
        await message.answer('❌ Произошла ошибка при добавлении вопроса')
    
    await state.clear()

@admin_router.callback_query(F.data == 'cancel_add')
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('❌ Добавление вопроса отменено')

@admin_router.message(Command('apanel'))
async def apanel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('❌ У вас нет прав для выполнения этой команды.')
        return
    
    buttons = [
        ['➕ Добавить вопрос', 'add_question'],
        ['📋 Список вопросов', 'list_questions'],
        ['📊 Статистика', 'admin_stats']
    ]
    
    await message.answer(
        '🔰 **Админ-панель**\n\n'
        'Выберите действие:',
        reply_markup=create_inline_keyboard(buttons, 1)
    )

@admin_router.callback_query(F.data == 'add_question')
async def admin_add_question(callback: CallbackQuery, state: FSMContext):
    await start_add_question(callback.message, state)
    await callback.answer()