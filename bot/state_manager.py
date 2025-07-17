# your_bot_project/bot/state_manager.py

import logging
from config import State

logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages the conversation state and temporary data for each user.
    This replaces the need for a global user_data dictionary.
    """
    def __init__(self):
        self._user_states = {}

    def _ensure_user_exists(self, user_id: int):
        """Initializes a data structure for a user if they don't exist yet."""
        if user_id not in self._user_states:
            self._user_states[user_id] = {'state': State.START, 'data': {}}
            logger.info(f"New user state initialized for user_id: {user_id}")

    def set_state(self, user_id: int, state: int):
        """Sets the conversation state for a user."""
        self._ensure_user_exists(user_id)
        self._user_states[user_id]['state'] = state
        logger.debug(f"State for user {user_id} set to {state}")

    def get_state(self, user_id: int) -> int:
        """Gets the current conversation state for a user."""
        return self._user_states.get(user_id, {}).get('state', State.START)

    def set_data(self, user_id: int, key: str, value):
        """Stores a piece of data for the user's session."""
        self._ensure_user_exists(user_id)
        self._user_states[user_id]['data'][key] = value
        logger.debug(f"Data for user {user_id} updated: {{'{key}': {value}}}")

    def get_data(self, user_id: int) -> dict:
        """Gets all stored data for the user's session."""
        return self._user_states.get(user_id, {}).get('data', {})

    def clear_state(self, user_id: int):
        """Clears all state and data for a user after a conversation ends."""
        if user_id in self._user_states:
            del self._user_states[user_id]
            logger.info(f"State for user {user_id} cleared.")