import json
import os
from typing import Optional, Dict, Any

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'balance.json')


def load_balance(path: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate the game's balance configuration.

    Parameters
    ----------
    path:
        Optional path to the JSON file. When omitted the default balance file
        from the :mod:`data` directory is used.

    Returns
    -------
    dict
        Parsed balance data.

    Raises
    ------
    ValueError
        If the JSON contains obviously invalid values such as negative health
        or damage numbers.
    """
    path = path or _DATA_PATH
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    player = data.get('player', {})
    zombie = data.get('zombie', {})
    if player.get('hp', 1) <= 0 or zombie.get('hp', 1) <= 0:
        raise ValueError('Health values must be positive')
    if player.get('damage', 1) <= 0 or zombie.get('damage', 1) <= 0:
        raise ValueError('Damage values must be positive')
    return data


__all__ = ['load_balance']
