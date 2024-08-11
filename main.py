import asyncio
import discord
import os
import re
import subprocess

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID'))
SIGNAL_GROUP_ID = os.environ.get('SIGNAL_GROUP_ID')
SIGNAL_NUMBER = os.environ.get('SIGNAL_NUMBER')

def extract_signal_data(raw_data):
    sender_pattern = r'Envelope from:\s*“([^”]+)”\s*\+([0-9]+)\s*'
    group_id_pattern = r'Group info:\s*Id:\s*([^\s]+)'
    body_pattern = r'Body:\s*(.+)'

    sender_match = re.search(sender_pattern, raw_data)
    group_id_match = re.search(group_id_pattern, raw_data)
    body_match = re.search(body_pattern, raw_data)

    sender = sender_match.group(1) if sender_match else None
    group_id = group_id_match.group(1).rstrip('=') if group_id_match else None
    body = body_match.group(1) if body_match else None

    return sender, group_id, body

async def fetch_signal_messages():
    while True:
        process = await asyncio.create_subprocess_exec(
            'signal-cli', '-u', SIGNAL_NUMBER, 'receive',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await process.communicate()
            if stdout:
                raw_data = stdout.decode('utf-8')
                sender, group_id, body = extract_signal_data(raw_data)
                if group_id == SIGNAL_GROUP_ID:
                    await send_to_discord(f"{sender} (Signal): {body}")
            if stderr:
                print(f"Signal CLI error: {stderr.decode('utf-8')}")
        except Exception as e:
            print(f"Error fetching Signal messages: {e}")
        await asyncio.sleep(0.5)  # Adjust this as needed

async def send_to_discord(message):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(message)
    else:
        print("Channel not found.")

def send_to_signal(message):
    subprocess.run(
        ['signal-cli', '-u', SIGNAL_NUMBER, 'send', '-g', SIGNAL_GROUP_ID,
         '-m', message]
    )

class dcClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            self.synced = True
        print(f'Logged on as {self.user}')

    async def on_message(self, message):
        if message.channel.id == DISCORD_CHANNEL_ID\
        and message.author != self.user:
            send_to_signal(f"{message.author} (Discord): {message.content}")

client = dcClient()

async def main():
    await asyncio.gather(
        client.start(DISCORD_TOKEN),
        fetch_signal_messages(),
    )

if __name__ == "__main__":
    asyncio.run(main())

