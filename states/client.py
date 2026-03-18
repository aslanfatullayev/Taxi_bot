from aiogram.fsm.state import State, StatesGroup

class ClientRegistrationFSM(StatesGroup):
    """FSM for registering a new client."""
    waiting_name = State()
    waiting_phone = State()

class ClientCancelOrderFSM(StatesGroup):
    """FSM for client cancelling an active order and providing a reason."""
    waiting_reason = State()

class ComplaintFSM(StatesGroup):
    """FSM for filing a complaint about a driver."""
    waiting_driver_name = State()
    waiting_driver_phone = State()
    waiting_reason = State()

