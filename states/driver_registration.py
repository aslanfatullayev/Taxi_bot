from aiogram.fsm.state import State, StatesGroup


class DriverRegistrationFSM(StatesGroup):
    """Multi-step driver registration flow."""
    waiting_name = State()
    waiting_phone = State()
    waiting_car_model = State()
    waiting_car_number = State()
