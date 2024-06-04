from api import AlistClient, FileInfo
import asyncio

client = AlistClient('')

total = 0

async def callback(file: FileInfo):
    global total
    total += file.size
    print(f'{file.path} {file.size / 1024 / 1024}MB {total / 1024 / 1024 / 1024}GB')

files = asyncio.run(client.walk(callback))
