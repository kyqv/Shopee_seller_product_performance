from ..module import Shopee
from ...logs import log
import logging
import time

logger = logging.getLogger('robot')

class mission:
    def __init__(self, user:str, pwd:str, headless:bool=False, cookies:list=[]) -> dict:
        self.user = user
        self.pwd = pwd
        self.headless = headless
        self.cookies = cookies

    def robot(self):
        # 啟動蝦皮
        shopee = Shopee.module(user=self.user, pwd=self.pwd, headless=self.headless)
        if self.cookies:
            login_result = shopee.no_need_login(cookies=self.cookies)
            if not login_result['success']:
                login_result = shopee.login()
        else:
            login_result = shopee.login()
        if not login_result['success']:
            return login_result 
        
        # 捕捉賣場列表
        store_list_result = shopee.crawl_store_list()
        if not store_list_result['success']:
            # 取得cookies
            cookies = shopee.get_cookies()
            store_list_result['cookies'] = cookies
            return store_list_result
        
        # 捕捉數據
        result = []
        last_data = len(store_list_result['data']) - 1
        for index, data in enumerate(store_list_result['data']):
            logger.info(f"共{len(store_list_result['data'])}個賣場, 目前第{index+1}個賣場")
            switch_result = shopee.switch_store(store=data['name'])
            if not switch_result['success']:
                # 取得cookies
                cookies = shopee.get_cookies()
                switch_result['cookies'] = cookies
                return switch_result
            logger.info(f'賣場:{data["name"]}, 進行捕捉')
            center_result = shopee.Product_Performance(store=data['id'])
            if not center_result['success']:
                # 取得cookies
                cookies = shopee.get_cookies()
                center_result['cookies'] = cookies
                return center_result
            result += center_result['data']
            logger.info(f"賣場共:{len(center_result['data'])}筆商品資料")
            logger.info(f'賣場:{data["name"]}, 數據獲取成功')
            if index != last_data:
                time.sleep(60)
        # 取得cookies
        cookies = shopee.get_cookies()
        logger.info('取得cookies成功')
        # 結束任務
        shopee.driver_close()
        logger.info('爬蟲關閉成功')
        return {'success':True, 'message':'', 'data':result, 'cookies':cookies}
            
            


        