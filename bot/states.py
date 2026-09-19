from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    adult = State()
    consent = State()
    username = State()
    name = State()
    age = State()
    gender = State()
    seeking = State()
    location = State()
    bio = State()
    photo = State()
    preview = State()


class Edit(StatesGroup):
    value = State()


class Search(StatesGroup):
    age = State()


class Complaint(StatesGroup):
    reason = State()
    comment = State()
    confirm = State()
