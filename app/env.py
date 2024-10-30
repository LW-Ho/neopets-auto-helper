import json
from dataclasses import dataclass
from typing import List

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
    GMAIL_NOTIFY: dict

@dataclass
class NEOAccountsData:
    accounts: List[NEOAccount] 

with open('accounts.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

accounts = [NEOAccount(**account_data) for account_data in data.values()]
NEOACCOUNT_DATA = NEOAccountsData(accounts=accounts)