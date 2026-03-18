from aiogram.fsm.state import State, StatesGroup


class OrderFSM(StatesGroup):
    """States for the client order flow."""
    waiting_from = State()   # Waiting for "pickup" location
    waiting_to = State()     # Waiting for "destination" location
    confirm = State()        # Waiting for order confirmation
