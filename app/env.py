import json
import os
from dataclasses import dataclass, field

@dataclass
class NEOAccount:
    LEGACY: bool
    PIN_CODE: str
    USERNAME: str
    PASSWORD: str
    NEOPASS_USERNAME: str
    ACTIVE_PET_NAME: str
    BANK_INTEREST_FLAG: bool
    BUY_STOCK_FLAG: bool
    SELL_STOCK_FLAG: bool
    TRUDYS_FLAG: bool
    JELLY_FLAG: bool
    OMELETTE_FLAG: bool
    FISHING_FLAG: bool
    SPRINGS_FLAG: bool
    FRUIT_FLAG: bool
    SHRINE_FLAG: bool
    TOMBOLA_FLAG: bool
    TDMBGPOP_FLAG: bool
    ADVENTCALENDAR_FLAG: bool
    PETLAB_FLAG: bool
    PETLAB_NAME: str
    PETPETLAB_FLAG: bool
    PETPETLAB_NAME: str
    TVW_EVENT_FLAG: bool
    TRAINING_SWASHBUCKLING_ACADEMY: dict
    TRAINING_MYSTERY_ISLAND: dict
    TRAINING_SECRET_NINJA: dict
    AUTO_SAVE_TO_SAFTY_BOX: bool
    GMAIL_NOTIFY: dict = field(default_factory=dict)
    # NOTIFY_METHOD selects which channel(s) receive run summaries:
    # "gmail", "telegram", or "both"/"all" (a list of channels is also accepted).
    NOTIFY_METHOD: str = "gmail"
    TELEGRAM_NOTIFY: dict = field(default_factory=dict)

# Default account file used when ACCOUNT_FILE is not set. One container == one
# account: point ACCOUNT_FILE at a single-account JSON (see account.example.json).
DEFAULT_ACCOUNT_FILE = "account.json"


def load_account(path: str | None = None) -> NEOAccount:
    '''
    Load one account from a single-account JSON file. Path resolution:
    explicit ``path`` arg -> ACCOUNT_FILE env var -> DEFAULT_ACCOUNT_FILE.
    The file must be a flat single-account object (see account.example.json).
    '''
    path = path or os.environ.get("ACCOUNT_FILE", DEFAULT_ACCOUNT_FILE)

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "USERNAME" not in data:
        raise ValueError(
            f"{path} is not a single-account file. It must be a flat JSON object with "
            "the account fields at the top level (see account.example.json)."
        )

    return NEOAccount(**data)
