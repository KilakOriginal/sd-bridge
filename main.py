import aiofiles
import aiohttp
import asyncio
import discord
import os
from pathlib import Path
import re
import subprocess

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID'))
SIGNAL_GROUP_ID = os.environ.get('SIGNAL_GROUP_ID')
SIGNAL_NUMBER = os.environ.get('SIGNAL_NUMBER')
THIS_DIR = os.path.dirname(os.path.realpath(__file__))
TEMP_DIR = f"{THIS_DIR}/.temp"

def extract_signal_data(raw_data: str) -> tuple:
    sender_pattern = r'Envelope from:\s*“([^”]+)”\s*\+([0-9]+)\s*'
    group_id_pattern = r'Group info:\s*Id:\s*([^\s]+)'
    body_pattern = r'Body:\s*(.+)'
    attachment_pattern = r'Stored plaintext in:\s*(.+)'

    sender_match = re.search(sender_pattern, raw_data)
    group_id_match = re.search(group_id_pattern, raw_data)
    body_match = re.search(body_pattern, raw_data)
    attachment_match = re.search(attachment_pattern, raw_data)

    sender = sender_match.group(1) if sender_match else "Unknown"
    group_id = group_id_match.group(1).rstrip('=') if group_id_match else None
    body = body_match.group(1) if body_match else ""
    attachment = attachment_match.group(1) if attachment_match else None

    return sender, group_id, body, attachment

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
                sender, group_id, body, attachment =\
                    extract_signal_data(raw_data)
                if group_id == SIGNAL_GROUP_ID:
                    await send_to_discord(f"{sender} (Signal): {body}",
                                          attachment)
            if stderr:
                print(f"Signal CLI error: {stderr.decode('utf-8')}")
        except Exception as e:
            print(f"Error fetching Signal messages: {e}")
        await asyncio.sleep(0.5)  # Adjust this as needed

async def send_to_discord(message: str, attachment: str = None):
    file = []
    if attachment:
        try:
            file = [discord.File(attachment)]
        except (FileNotFoundError, IOError) as e:
            print(f"Failed to attach file {attachment}: {e}")
            message = f"{message} [Failed to attach a file]"
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(content=message, files=file)
    else:
        print("Channel not found.")

def send_to_signal(message: str, attachment: str = None):
    command = ['signal-cli', '-u', SIGNAL_NUMBER, 'send', '-g',
               SIGNAL_GROUP_ID, '-m', message]
    if attachment:
        command.extend(['-a', attachment])
    subprocess.run(command)

async def download_attachment(url, filename):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url,
                                   timeout=aiohttp.ClientTimeout(total=60))\
                                           as response:
                if response.status == 200:
                    async with aiofiles.open(filename, 'wb') as f:
                        while True:
                            chunk = await response.content.read(65536) #64KiB
                            if not chunk:
                                break
                            await f.write(chunk)
                    return filename
                else:
                    print(f"Failed to download attachment: {response.status}")
                    return None
    except Exception as e:
        print(f"Error downloading attachment: {e}")
        return None

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
            attachment_paths = []
            if message.attachments:
                Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
                for attachment in message.attachments:
                    attachment_paths.append(
                            await download_attachment(attachment.url,
                                        f"{TEMP_DIR}/{attachment.filename}"))
                send_to_signal(f"{message.author} (Discord): \
                        {message.content}", attachment_paths[0])
                for path in attachment_paths[1:]:
                    send_to_signal(f"{message.author} (Discord):", path)
                
                for path in attachment_paths:
                    if os.path.exists(path):
                        os.remove(path)

client = dcClient()

async def main():
    await asyncio.gather(
        client.start(DISCORD_TOKEN),
        fetch_signal_messages(),
    )

if __name__ == "__main__":
    asyncio.run(main())

