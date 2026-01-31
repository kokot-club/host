import os
import requests

DISCORD_APP_CLIENT_ID = os.environ.get('DISCORD_APP_CLIENT_ID')
DISCORD_APP_CLIENT_SECRET = os.environ.get('DISCORD_APP_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
DISCORD_SERVER_ID = os.environ.get('DISCORD_SERVER_ID')

class Discord:
    _api_base = 'https://discord.com/api/'

    @staticmethod
    def _bot_headers(bot_token):
        return {'Authorization': f'Bot {bot_token}'}

    @staticmethod
    def _bearer_headers(access_token):
        return {'Authorization': f'Bearer {access_token}'}

    @staticmethod
    def send_dm(discord_user_id, content):
        dm = requests.post(
            f'{Discord._api_base}/v10/users/@me/channels',
            headers=Discord._bot_headers(bot_token=DISCORD_BOT_TOKEN),
            json={'recipient_id': discord_user_id}
        ).json()

        channel_id = dm.get('id') if dm else None
        if not channel_id:
            return False

        requests.post(
            f'{Discord._api_base}/v10/channels/{channel_id}/messages',
            headers=Discord._bot_headers(bot_token=DISCORD_BOT_TOKEN),
            json={'content': content}
        )
        return True

    @staticmethod
    def exchange_oauth_code(code, redirect_uri):
        return requests.post(
            f'{Discord._api_base}/oauth2/token',
            data={
                'client_id': DISCORD_APP_CLIENT_ID,
                'client_secret': DISCORD_APP_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            }
        ).json()

    @staticmethod
    def get_user_info(access_token):
        return requests.get(
            f'{Discord._api_base}/users/@me',
            headers=Discord._bearer_headers(access_token=access_token)
        ).json()

    @staticmethod
    def add_user_to_guild(server_id, user_id, access_token):
        requests.put(
            f'{Discord._api_base}/guilds/{server_id}/members/{user_id}',
            headers=Discord._bearer_headers(access_token=access_token)
        )
