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
    TVW_HP_PET_NAME_1: str
    TVW_HP_PET_NAME_2: str
    BANK_INTEREST_FLAG: bool
    TRUDYS_FLAG: bool
    JELLY_FLAG: bool
    OMELETTE_FLAG: bool
    FISHING_FLAG: bool
    SPRINGS_FLAG: bool
    FRUIT_FLAG: bool
    TVW_EVENT_FLAG: bool
    AUTO_SAVE_TO_SAFTY_BOX: bool

@dataclass
class NEOAccountsData:
    accounts: List[NEOAccount] 

with open('accounts.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

accounts = [NEOAccount(**account_data) for account_data in data.values()]
NEOACCOUNT_DATA = NEOAccountsData(accounts=accounts)