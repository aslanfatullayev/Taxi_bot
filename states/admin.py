from aiogram.fsm.state import State, StatesGroup

class AdminAddDriverFSM(StatesGroup):
    """Admin flow for adding a driver manually."""
    waiting_user_id = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_car_model = State()
    waiting_car_number = State()

class AdminAuthFSM(StatesGroup):
    """FSM for secondary admin login."""
    waiting_code = State()

class AdminChangeCodeFSM(StatesGroup):
    """FSM for main admin to change the access code."""
    waiting_new_code = State()
