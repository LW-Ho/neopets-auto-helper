from app.gmail import GmailNotify
from app.telegram import TelegramNotify


class Notifier():
    '''
    Fan-out notifier. Holds one or more channel notifiers (Gmail, Telegram) and
    dispatches ``notify(method, message)`` to every active channel. Which
    channels are active is decided by ``NOTIFY_METHOD`` in the account config
    (see ``build_notifier``). A failure in one channel never blocks the others.
    '''

    def __init__(self, channels: list) -> None:
        self._channels = channels

    def notify(self, method: str = '', message: dict = {}) -> None:
        for channel in self._channels:
            try:
                channel.notify(method, message)
            except Exception as e:
                print(f'notify channel error {e}')


def _normalize_methods(notify_method) -> list:
    '''
    NOTIFY_METHOD may be a string ("gmail", "telegram", or "both"/"all") or a
    list of channel names. Returns a lowercase list of channel names.
    '''
    if not notify_method:
        return []
    if isinstance(notify_method, str):
        value = notify_method.strip().lower()
        if value in ('both', 'all'):
            return ['gmail', 'telegram']
        return [value]
    return [str(m).strip().lower() for m in notify_method]


def build_notifier(neoaccount) -> Notifier:
    '''
    Build a Notifier from an account's config. NOTIFY_METHOD selects the
    channel(s); each channel is only added when its config block is present.
    '''
    methods = _normalize_methods(getattr(neoaccount, 'NOTIFY_METHOD', 'gmail'))
    channels = []

    gmail_cfg = getattr(neoaccount, 'GMAIL_NOTIFY', None) or {}
    if 'gmail' in methods and gmail_cfg:
        channels.append(GmailNotify(
            gmail_cfg.get('APPLICATION_TOKEN', ''),
            gmail_cfg.get('SENDER_GMAIL', ''),
            gmail_cfg.get('RECEIVER_EMAIL', ''),
        ))

    telegram_cfg = getattr(neoaccount, 'TELEGRAM_NOTIFY', None) or {}
    if 'telegram' in methods and telegram_cfg:
        channels.append(TelegramNotify(
            telegram_cfg.get('BOT_TOKEN', ''),
            telegram_cfg.get('CHAT_ID', ''),
        ))

    return Notifier(channels)
