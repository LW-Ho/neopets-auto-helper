# neopets-auto-helper

This project uses Python Playwright to achieve asynchronous operations for completing tasks on Neopets.

# How to config my neopets account
Please follow the fields in the accounts.json file to set up the accounts: <br>
Set `LEGACY` to ==True== if the account has not yet been linked to NeoPass. <br>
Set `USERNAME` and `PASSWORD` as the account's username and password.<br>
If set to ==False==, please input the NeoPass email and password for `USERNAME` and `PASSWORD`, and input the Neopets username for `NEOPASS_USERNAME`.

# How to run

Please use Python and install the required packages from `requirements.txt`. After updating `accounts.json`, you can run `main.py`, which will handle all the tasks.

```
# source venv...
pip install -r requirements.txt
python main.py
```

# Inclouded Features

- Bank Collect
- Fishing
- Fruit
- Jelly
- Omelette
- Springs
- Trudys
- Shrine
- Tombola
- Tdmbgpop
- The Void Within Event
    - Hosiptal
    - Void Location
- Buy Stoks
- PetLab    # First, You need to collect map to open.
- PetpetLab # First, You need to collect map to open.

# Coming Features
- Shop Wizard
- Training School
    - Cap'n Threelegs' Swashbuckling Academy
    - Mystery Island Training School
    - Secret Ninja Training School
- Battledome
- Daily Quests
