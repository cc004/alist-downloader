from api import AlistClient, FileInfo
import asyncio, os
import aiohttp

client = AlistClient('')

total = 0
max_downloading = 8
downloading = 0

clients = []

class checker:
    def __init__(self, cacheFile):
        try:
            with open(cacheFile, 'r', encoding='utf8') as f:
                self.cache = set(f.read().splitlines())
        except:
            self.cache = set()
        self.fp = open(cacheFile, 'a', encoding='utf8')
    
    def check(self, url):
        return url in self.cache
    
    def add(self, url):
        self.cache.add(url)
        self.fp.write(url + '\n')
        self.fp.flush()

downloaded_checker = checker('cache.txt')
total = 0

async def callback(file: FileInfo):
    global downloading, max_downloading, total

    if downloaded_checker.check(file.path):
        return

    while downloading >= max_downloading:
        await asyncio.sleep(1)
        
    try:
        if downloading == len(clients):
            clients.append(aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_read=10, sock_connect=10)))
            
        http = clients[downloading]
        
        downloading += 1

        local_path = '.' + file.path
        
        if os.path.exists(local_path):
            local_total = os.path.getsize(local_path)
            if local_total == file.size:
                print(f'File {local_path} already exists and size verified')
                downloaded_checker.add(file.path)
                total += file.size
                return
            else:
                print(f'File {local_path} already exists but size mismatch (local: {local_total}, remote: {file.size})')
        
        file = await client.get(file.path)
        resp = await http.get(file.raw_url)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        bytes_to_write = b''

        with open(local_path, 'wb') as fp:
            async for data in resp.content.iter_chunked(10 * 1024 * 1024):
                fp.write(data)
        
        print(f'Downloaded {file.path} {file.size / 1024 / 1024}MB')
        
    except Exception as e:
        print(f'Error: {file.path} {e}')
        import traceback
        traceback.print_exc()
    finally:
        downloading -= 1

files = asyncio.run(client.walk(callback))
print('downloaded: {} TB'.format(total / 1024 / 1024 / 1024 / 1024))