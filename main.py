import discord
import webhook

#AwSW Fan Discord


class Scraper(discord.Client):
    async def on_ready(self):
        server_list = list(self.servers)
        for i, server in enumerate(server_list):
            print("{}: {}".format(i, server))
        num = int(input("Type server number: "))
        server = server_list[num]
        print("Cloning {}".format(server))
        print([channel.name for channel in server.channels])
        clone = await self.create_server(server.name)
        for channel in server.channels:
            if channel.type is not discord.ChannelType.text:
                continue
            new = await self.create_channel(clone, channel.name)
            hook = await self.create_webhook(new, "Clone", None)
            try:
                messages = await self.get_channel_messages(channel)
            except discord.errors.Forbidden:
                await hook.execute(content="This channel isn't readable by you",
                                   username="Clone Bot")
            except discord.errors.NotFound:
                await hook.execute(content="This channel wasn't found and isn't readable",
                                   username="Clone Bot")
            else:
                for i, message in enumerate(reversed(messages)):
                    if i % 100 == 0:
                        print("{}: {}/{}".format(channel, i, len(messages)))
                    files = []
                    for attachment in message.attachments:
                        url = await self.http.session.request("GET", attachment["url"])
                        files.append((await url.read(), attachment["filename"]))
                    try:
                        await hook.execute(content=message.clean_content,
                                           username=message.author.name,
                                           embed=message.embeds,
                                           avatar_url=message.author.avatar_url,
                                           files=files)
                    except discord.errors.HTTPException:
                        pass
        print("Done")

    async def create_webhook(self, channel, name, avatar_url):
        return await webhook.Webhook.create_webhook(self.http, channel, name, avatar_url)

    async def get_webhooks(self, channel):
        return await webhook.Webhook.get_webhooks(self.http, channel)

    async def get_webhook(self, channel, name):
        webhooks = await self.get_webhooks(channel)
        return discord.utils.get(webhooks, name=name)

    async def get_channel_messages(self, channel, at_once=100):
        message_list = []
        before = None
        done = False
        while not done:
            i = 0
            async for message in self.logs_from(channel, before=before, limit=at_once):
                message_list.append(message)
                i += 1
            if i == 0 and not message_list:
                return []
            elif i != at_once:
                done = True
            else:
                before = message
        return message_list


if __name__ == "__main__":
    bot = Scraper()
    bot.run("username", "password")
