from discord.utils import _bytes_to_base64_data
from discord.http import Route
from discord.user import User
from discord.utils import snowflake_time, to_json
from discord.embeds import Embed
import aiohttp


class Webhook:
    def __init__(self, id, server, channel, user, name, avatar, token, http):
        self.id = id
        self.server = server
        self.channel = channel
        self.created_by = User(**user)
        self.name = name
        self.avatar = avatar
        self.token = token
        self._http = http

    def __repr__(self):
        return "<Webhook name={}, guild_id={}, channel_id={} user={}>".format(
            repr(self.name),
            self.server.id,
            self.channel.id,
            self.created_by
        )

    async def execute(self, content=None, files=None, embed=None, username=None, avatar_url=None, tts=False):
        payload = {
            "tts": tts
        }
        if content:
            payload["content"] = content
        if embed:
            payload['embeds'] = embed
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if files is None: files = []
        form = aiohttp.FormData()
        form.add_field('payload_json', to_json(payload))
        for file, filename in files:
            form.add_field('file', file, filename=filename, content_type='application/octet-stream')

        r = Route('POST', '/webhooks/{webhook_id}/{token}', webhook_id=self.id, token=self.token)
        await self._http.request(r, data=form)

    @property
    def created_at(self):
        """Returns the user's creation time in UTC.

        This is when the user's discord account was created."""
        return snowflake_time(self.id)

    @classmethod
    async def create_webhook(cls, http, channel, name, avatar_url):
        if avatar_url is not None:
            avatar_f = await http.session.request("GET", avatar_url)
            payload = {
                "name": name,
                "avatar": _bytes_to_base64_data(await avatar_f.read())
            }
            avatar_f.close()
        else:
            payload = {"name": name}
        r = Route('POST', '/channels/{channel_id}/webhooks', channel_id=channel.id)
        json = await http.request(r, json=payload)
        return cls.create_from_json(json, channel, http)

    @classmethod
    async def get_webhooks(cls, http, channel):
        r = Route('GET', '/channels/{channel_id}/webhooks', channel_id=channel.id)
        json = await http.request(r)
        return [cls.create_from_json(webhook, channel, http) for webhook in json]

    @classmethod
    def create_from_json(cls, json, channel, http):
        return cls(id=json["id"],
                   server=channel.server,
                   channel=channel,
                   user=json["user"],
                   name=json["name"],
                   avatar=json["avatar"],
                   token=json["token"],
                   http=http)
