from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def create_inline_keyboard(buttons: list, width: int = 2) -> InlineKeyboardMarkup:
    """
    Создает инлайн клавиатуру
    :param buttons: список кнопок в формате [['текст', 'callback_data'], ...]
    :param width: количество кнопок в ряду
    """
    builder = InlineKeyboardBuilder()
    
    for button in buttons:
        builder.add(InlineKeyboardButton(
            text=button[0],
            callback_data=button[1]
        ))
    
    builder.adjust(width)
    return builder.as_markup()