import aiorequests, asyncio
from typing import List, Iterator, Callable, Coroutine

class FileInfo:
    def __init__(self, obj, path, parent: 'AlistClient'):
        self.parent = parent
        self.name = obj['name']
        self.size = obj['size']
        self.is_dir = obj['is_dir']
        self.sign = obj['sign']
        self.raw_url = obj.get('raw_url', None)
        self.path = path
    
    async def get(self):
        return await self.parent.get(self.path)

class AlistClient:
    def __init__(self, root):
        self.root = root
        self.password = ''
        self.api_limit = 8
        self.running_api = 0
        
    async def _api(self, path, obj):
        while self.running_api == self.api_limit:
            await asyncio.sleep(1)

        while True:
            try:
                self.running_api += 1
            
                resp = await aiorequests.post(
                    self.root + path,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    json=obj,
                    timeout=10
                )
                obj0 = await resp.json()
                assert obj0['code'] == 200
                return obj0['data']
            except:
                pass
            finally:
                self.running_api -= 1
    
    async def list(self, path = '') -> Iterator[FileInfo]:
        resp = await self._api('/api/fs/list', {
            'path': path,
            'password': self.password,
            'page': 1,
            'per_page': 0,
            'refresh': False
        })
        if not resp['total'] and not resp['content']:
            return iter([])
        assert resp['total'] == len(resp['content'])
        return (FileInfo(obj, path + '/' + obj['name'], self) for obj in resp['content'])
    
    async def get(self, path) -> FileInfo:
        resp = await self._api('/api/fs/get', {
            'path': path,
            'password': self.password
        })
        
        return FileInfo(resp, path, self)

    async def walk(self, callback: Callable[[FileInfo], Coroutine], path = '') -> None:
        objs = await self.list(path)
        async def with_one(obj):
            if obj.is_dir:
                await self.walk(callback, obj.path)
            else:
                await callback(obj)
        await asyncio.gather(*(with_one(obj) for obj in objs))
