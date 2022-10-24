import os
import time
import httpx
import asyncio
from lxml import etree
from PyQt5.QtCore import QThread, pyqtSignal

GREEN = '\033[92m'
RED = '\33[31m'
BLUE = '\33[34m'
END = '\33[0m'


class Grab(QThread):
    process_signal = pyqtSignal(int, int)
    update_text_signal = pyqtSignal(str)

    def __init__(self, keyword, proxies, folder='./download'):
        super(Grab, self).__init__()
        self.keyword = keyword
        self.search_url = 'https://asiantolick.com/ajax/buscar_posts.php?search={}&index={}'
        self.proxies = proxies
        self.header = ''
        self.folder = folder
        self.count = 0
        self.total = 0

    def __del__(self):
        self.wait()

    def search(self):
        __urls = []
        index = 0
        with httpx.Client(proxies=self.proxies) as client:
            while True:
                url_parts = self.search_html(client, self.search_url.format(self.keyword, index))
                if len(url_parts) == 0:
                    break
                __urls.extend(url_parts)
                index += 1

        self.total = len(__urls)
        self.count = 0
        return __urls

    def search_html(self, client, url):
        url_parts = []
        retry = 0
        while retry < 5:
            try:
                ret_bytes = client.get(url=url, headers=self.header)
                ret_html = ret_bytes.content.decode('utf-8')
                html = etree.HTML(ret_html)
                url_parts = [str(_url) for _url in html.xpath('//*[@mob="0"]/@href')]
                return url_parts
            except httpx.TimeoutException:
                time.sleep(1)
                retry += 1
        return url_parts

    async def init_page_tasks(self, _urls):
        page_tasks = [self.single_page_task(url) for url in _urls]
        await self.sem_gather(page_tasks, 5)

    async def sem_gather(self, tasks, sem_num):
        sem = asyncio.Semaphore(sem_num)

        async def _wrapper(task):
            async with sem:
                return await task

        _tasks = map(_wrapper, tasks)
        return await asyncio.gather(*_tasks)

    async def single_page_task(self, url):
        task_name = url.split('/')[-1]
        print(f'>>[{GREEN}{self.count}/{self.total}{END}] Start page task. {task_name}')
        self.update_text_signal.emit(f'>>[{self.count}/{self.total}] Start page task. {task_name}')

        async with httpx.AsyncClient(proxies=self.proxies) as client:
            for _ in range(5):
                try:
                    ret = await client.get(url=url, headers=self.header)
                    break
                except Exception:
                    print(
                        f'>>[{GREEN}{self.count}/{self.total}{END}] {BLUE}Retry page task {_} times {END},{task_name}')
                    self.update_text_signal.emit(
                        f'>>[{self.count}/{self.total}] Retry page task {_} times ,{task_name}')
                    time.sleep(1)
                    pass
            else:
                print(
                    f'>>[{GREEN}{self.count}/{self.total}{END}] {RED} Error in page task request.{END} {task_name}')
                self.update_text_signal.emit(f'>>[{self.count}/{self.total}]  Error in page task request. {task_name}')
                return
        print(f'>>[{GREEN}{self.count}/{self.total}{END}] Request page task done. {task_name}')
        self.update_text_signal.emit(f'>>[{self.count}/{self.total}] Request page task done. {task_name}')

        ret_html = ret.content.decode('utf-8')
        ret_etree = etree.HTML(ret_html)
        resource_urls = [str(resouce) for resouce in ret_etree.xpath('//div[@data-src]/@data-src')]
        title = str(ret_etree.xpath('//h1[@style]')[0].text).strip()
        download_tasks = [self.single_download_task(title, _r_url) for _r_url in resource_urls]
        await self.sem_gather(download_tasks, 5)

        self.count += 1
        print(f'>>[{GREEN}{self.count}/{self.total}{END}] Done. {task_name}')
        self.update_text_signal.emit(f'>>[{self.count}/{self.total}] Done. {task_name}')

        self.process_signal.emit(self.count, self.total)

    # download
    async def single_download_task(self, folder_name, r_url):
        file_name = r_url.split('/')[-1]
        # print(f'>>>> Start download task. {folder_name}/{file_name}')
        self.update_text_signal.emit(f'>>>> Start download task. {folder_name}/{file_name}')

        async with httpx.AsyncClient(proxies=self.proxies) as client:
            for _ in range(5):
                try:
                    ret = await client.get(url=r_url, headers=self.header)
                    break
                except Exception:
                    print(f'>>>> {BLUE}Retry download task {_} times.{END} {folder_name}/{file_name}')
                    self.update_text_signal.emit(f'>>>> Retry download task {_} times. {folder_name}/{file_name}')
                    pass
            else:
                print(f'>>>> {RED} Error in download task request.{END} {folder_name}/{file_name}')
                self.update_text_signal.emit(f'>>>>  Error in download task request. {folder_name}/{file_name}')
                return

        path = f'{self.folder}/{self.keyword}/{folder_name}'
        if path.__contains__(':'):
            path = path.replace(':', '_')
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{file_name}', 'wb+') as f:
            f.write(ret.content)

        # print(f'>>>> Done download task. {folder_name}/{file_name}')
        self.update_text_signal.emit(f'>>>> Done download task. {folder_name}/{file_name}')

    def run(self):
        urls = self.search()
        asyncio.run(self.init_page_tasks(urls))


if __name__ == '__main__':
    _proxies = {
        'http://': 'http://127.0.0.1:7890',
        'https://': 'http://127.0.0.1:7890',
    }
    Grab(keyword='neko', proxies=_proxies).run()
