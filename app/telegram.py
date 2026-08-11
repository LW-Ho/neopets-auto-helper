import json
import requests

# Telegram messages are capped at 4096 characters; leave room for the title/format.
_MAX_MESSAGE_LEN = 4096


class TelegramNotify():
    '''
    Send run summaries to a Telegram chat via the Bot API.

    Mirrors GmailNotify's interface: ``notify('ok'|'error', message_dict)``.
    The channel is a no-op (returns False) when BOT_TOKEN or CHAT_ID is empty,
    so it can be safely constructed even when Telegram is not configured.
    '''

    API_URL = 'https://api.telegram.org/bot{token}/sendMessage'

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id

    def notify(self, method: str = '', message: dict = {}) -> bool:
        body = json.dumps(
            message, indent=4, sort_keys=True, ensure_ascii=False)

        if not self._bot_token or not self._chat_id:
            print(f'Telegram notify was disabled {body}')
            return False

        if method == 'ok':
            title = '[INFO] Running neopets-auto-helper'
        elif method == 'error':
            title = '[ERROR] Login failed neopets-auto-helper'
        else:
            title = '[INFO] neopets-auto-helper'

        text = f'{title}\n{body}'
        if len(text) > _MAX_MESSAGE_LEN:
            text = text[:_MAX_MESSAGE_LEN - 3] + '...'

        try:
            print(f'start sending telegram {method}')
            resp = requests.post(
                self.API_URL.format(token=self._bot_token),
                json={'chat_id': self._chat_id, 'text': text},
                timeout=15,
            )
            if resp.status_code != 200:
                print(f'{__name__} error {resp.status_code} {resp.text}')
                return False
        except Exception as e:
            print(f'{__name__} error {e}')
            return False

        return True
