from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver import ActionChains
import datetime
import pytz
import easyimap
import requests_html
import time
import traceback
import requests
import pandas as pd
import logging
from ...logs import log
from pathlib import Path
from itertools import groupby
import warnings
#略過警告
warnings.simplefilter("ignore")
logger = logging.getLogger('robot')

#創建下載地址
path = Path('lib/download/')
if path.exists():
    for i in path.iterdir():
        i.unlink()
else:
    path.mkdir()

class module:
    def __init__(self, user, pwd, headless=False):
        self.user = user
        self.pwd = pwd
        self.headless = headless
    # 登入
    def login(self):
        while True:
            try:
                tz = pytz.timezone('Asia/Taipei')
                options = webdriver.ChromeOptions()
                # 設定下載網址
                prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': str(path.absolute())}
                options.add_experimental_option('prefs', prefs)
                #options.add_argument('blink-settings=imagesEnabled=false') #不加截圖片, 加速爬取
                # if self.headless:
                #     options.add_argument("--headless")
                self.driver = webdriver.Chrome('chromedriver', chrome_options=options)
                # 登入
                self.driver.get('https://seller.shopee.tw/account/signin')
                WebDriverWait(self.driver, 10, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'signin')))
                self.driver.find_element_by_css_selector('button[class="shopee-button shopee-button--large"]').click()
                WebDriverWait(self.driver, 10, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'main-card')))
                self.driver.find_element_by_css_selector('input[type="text"]').send_keys(self.user)
                time.sleep(1)
                self.driver.find_element_by_css_selector('input[type="password"]').send_keys(self.pwd)
                time.sleep(1)
                self.driver.find_element_by_css_selector('button[class="shopee-button login-btn shopee-button--primary shopee-button--large shopee-button--block"]').click()
                time.sleep(3)
                now_date = int((datetime.datetime.now(tz=tz) - datetime.timedelta(seconds=60)).timestamp())
                # 驗證
                if '登入驗證' in self.driver.page_source:
                    # 點擊用信寄收取驗證碼
                    self.driver.find_element_by_css_selector('button[class="shopee-button shopee-button--link shopee-button--normal"]').click()
                    while True:
                        if '操作過於頻繁' in self.driver.page_source:
                            return {'success':False, 'message':'操作過於頻繁，請過幾分鐘或一天後再試', 'cookies':[]}
                        vc = self.fetch_messages(user='juns_chen@rainforestretail.com.tw', pwd='Juns1984', date=now_date)
                        if vc:
                            break
                        else:
                            logger.info('尚未收到信, 暫停5秒')
                            time.sleep(5)
                            continue
                    self.driver.find_element_by_css_selector('input[placeholder="驗證碼"]').send_keys(vc)
                    time.sleep(0.5)
                    self.driver.find_element_by_css_selector('button[class="shopee-button login-btn shopee-button--primary shopee-button--large shopee-button--block"]').click()
                if '操作過於頻繁，請過幾分鐘或一天後再試' in self.driver.page_source:
                    logger.info('登入失敗操作過於頻繁，請過幾分鐘或一天後再試')
                    return {'success':False, 'message':'操作過於頻繁，請過幾分鐘或一天後再試'}
                logger.info('登入成功')
                return {'success':True, 'message':''}
            except Exception:
                logger.info('\n' + traceback.format_exc())
                self.driver.close()
                time.sleep(3)
                continue

    # 利用cookies登入
    def no_need_login(self, cookies):
        while True:
            try:
                # 測試cookies是否能用
                options = webdriver.ChromeOptions()
                # 設定下載網址
                prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': str(path.absolute())}
                options.add_experimental_option('prefs', prefs)
                #options.add_argument('blink-settings=imagesEnabled=false') #不加截圖片, 加速爬取
                # if self.headless:
                #     options.add_argument("--headless")
                self.driver = webdriver.Chrome('chromedriver', chrome_options=options)
                self.driver.get('https://seller.shopee.tw/')
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                time.sleep(1)
                self.driver.get('https://seller.shopee.tw/')
                WebDriverWait(self.driver, 10, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'sidebar-submenu-item-link')))
                return {'success':True, 'message':''}
            except TimeoutException:
                self.driver.close()
                logger.info('頁面錯誤, 將自動重登')
                return {'success':False, 'message':'頁面錯誤, 將自動重登'}
            except WebDriverException:
                self.driver.close()
                logger.info('連線異常, 即進行重試')
                time.sleep(3)
                continue
            
    # 取得信件驗證碼
    def fetch_messages(self, user, pwd, date):
        while True:
            try:
                vc = ''
                imapper = easyimap.connect('imap.gmail.com', user, pwd)
                for mail_id in imapper.listids(limit=6):  #用數字限制讀取信件
                    mail = imapper.mail(mail_id)
                    #蝦皮時區是UTC
                    if 'GMT' in mail.date:
                        continue
                    message_date = datetime.datetime.strptime(mail.date, '%a, %d %b %Y %H:%M:%S %z').timestamp()
                    if message_date > date and mail.title == 'Your Email OTP Verification Code':
                        result_html = mail.body
                        html = requests_html.HTML(html=result_html)
                        data = html.find('td[style="font-family: Helvetica, arial, sans-serif; font-size: 25px; color: #fc0404; text-align:center; line-height: 40px;"]')
                        vc = data[0].text.split('\n')[0] if data else ''
                        break
                    else:
                        continue
                return vc
            except:
                logger.info('\n' + traceback.format_exc())
                time.sleep(3)
                continue

    # 取得賣場列表
    def crawl_store_list(self):
        store_list =[]
        error_count = 0
        while True:
            try:
                # 判斷是否在首頁
                WebDriverWait(self.driver, 10, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'sidebar-submenu-item-link')))
                self.driver.get('https://seller.shopee.tw/portal/shop')
                # 判斷是否在賣場列表
                WebDriverWait(self.driver, 10, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'pagination')))
                # 用requests & driver.get_cookies() 取得賣場詳細資料
                session = requests.Session()
                cookies = self.driver.get_cookies()
                url = 'https://seller.shopee.tw/api/selleraccount/subaccount/get_shop_list/'
                for cookie in cookies:
                    session.cookies[cookie['name']] = cookie['value']
                resp = session.get(url)
                if resp.status_code != 200:
                    logger.info('發生錯誤請確認網路或可能蝦皮本身異常')
                    return {'success':False, 'message':f'status_code_Error:{resp.status_code}', 'data':[]}
                for shop in resp.json()['shops']:
                    store_list += [{'id':shop["shop_id"], 'name':shop["shop_name"].strip()}]
                # 回首頁
                self.driver.get('https://seller.shopee.tw/')
                logger.info('取得賣場列表成功')
                return {'success':True, 'message':'', 'data':store_list}

            except TimeoutException:
                error_count += 1
                logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(1)
                continue
            except NoSuchElementException:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生NoSuch可能改版, 請確認原因')
                return {'success':False, 'message':'發生NoSuch可能改版, 請確認原因', 'data':[]}
            except (
                    WebDriverException, 
                    requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout
                    ):
                error_count += 1
                logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(3)
                continue
            except Exception:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生未知異常, 請確認原因')
                return {'success':False, 'message':'發生未知異常, 請確認原因', 'data':[]}

    # 轉換賣場
    def switch_store(self, store):
        count = 0
        error_count = 0
        page = 1
        while True:
            try:
                if page == 1:
                    # 判斷是否在首頁
                    WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'sidebar-submenu-item-link')))
                    self.driver.get('https://seller.shopee.tw/portal/shop')
                else:
                    # 判斷其他頁面等3秒,self.driver.implicitly_wait()有問題
                    time.sleep(3)
                # 判斷是否在賣場列表
                WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'pagination')))
                # 取得列表
                html = requests_html.HTML(html=self.driver.page_source)
                datas = html.find('div.shop-list-container > div.shop-listing > div.shop-listing-container > div.shop-item-list')
                for index, data in enumerate(datas):
                    if data.text.split('\n',1)[0] != store:
                        continue
                    count = index+1
                    break
                # 取得頁數
                total_page = max([int(i) for i in html.find('ul.shopee-pager__pages', first=True).text.split('\n') if i.isdigit()])
                if not count and page < total_page:
                    page+=1
                    self.driver.find_element(by=By.CSS_SELECTOR, value='button.shopee-button.shopee-button--small.shopee-button--frameless.shopee-button--block.shopee-pager__button-next').click()
                    continue
                if count:
                    self.driver.find_element(by=By.CSS_SELECTOR, value=f'div.shop-item-list:nth-child({count})').click()
                    return {'success':True, 'message':'', 'data':[]}
                else:
                    return {'success':False, 'message':'查詢不到賣場, 請檢查程式', 'data':[]}
            except TimeoutException:
                error_count += 1
                # 判斷是否有跳出訊息
                result_window = self.popup_window()
                if (result_window['success'] and result_window['message']) or result_window['success'] is False:
                    logger.info(result_window['message'])
                if result_window['success'] and not result_window['message']:
                    logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                page = 1
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(1)
                continue
            except NoSuchElementException:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生NoSuch可能改版, 請確認原因')
                return {'success':False, 'message':'發生NoSuch可能改版, 請確認原因', 'data':[]}
            except WebDriverException:
                error_count += 1
                logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(3)
                continue
            except Exception:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生未知異常, 請確認原因')
                return {'success':False, 'message':'發生未知異常, 請確認原因', 'data':[]}

    # 賣家數據中心
    def Seller_Data_Center(self, store):
        error_count = 0
        while True:
            try:
                # 判斷回到主頁
                WebDriverWait(self.driver, 10, 2).until(EC.presence_of_element_located((By.CLASS_NAME,'sidebar-submenu-item-link')))
                self.driver.get('https://seller.shopee.tw/datacenter/dashboard')
                # 判斷是否在賣家中心
                WebDriverWait(self.driver, 10, 2).until(EC.presence_of_element_located((By.CLASS_NAME,'bi-date-input.track-click-open-time-selector')))
                # 捕捉數據總覽資料
                yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
                logger.info(f"捕捉數據日期:{yesterday}")
                y_start = int(datetime.datetime.strptime(yesterday + ' ' + '00:00', '%Y/%m/%d %H:%M').timestamp())
                y_end = int(datetime.datetime.strptime(yesterday + ' ' + '23:59', '%Y/%m/%d %H:%M').timestamp())
                up_dt = datetime.datetime.now()
                log_dt = datetime.datetime.now().replace(minute=0, second=0,microsecond=0)
                UpdateDate = up_dt.strftime('%Y-%m-%d %H:%M:%S')
                LogDate = log_dt.strftime('%Y-%m-%d %H:%M:%S')
                result = {}
                result['shopid'] = store
                result['TargetDate'] = yesterday
                url = f"https://seller.shopee.tw/api/mydata/v4/dashboard/export/?period=yesterday&start_ts={y_start}&end_ts={y_end}"
                cookies = self.driver.get_cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies[cookie['name']] = cookie['value']
                resp = session.get(url)
                if resp.status_code != 200:
                    logger.info('\n' + traceback.format_exc())
                    return {'success':False, 'message':'讀取EXCEL失敗:總覽', 'data':{}}
                Shippable_orders = pd.read_excel(resp.content,sheet_name='可出貨訂單').iloc[0]
                result['confirmed_gmv_shippableorder'] = Shippable_orders['總銷售額 (TWD)'].replace(',','')
                result['confirmed_orders_shippableorder'] = Shippable_orders['訂單總數'].replace(',','')
                result['cancelled_orders_shippableorder'] = Shippable_orders['不成立的訂單'].replace(',','')
                result['shop_uv_to_confirmed_buyers_rate_shippableorder'] = float(Shippable_orders['訂單轉換率(可出貨訂單)'].replace('%',''))
                result['shop_uv_shippableorder'] = Shippable_orders['訪客數'].replace(',','')
                result['shop_pv_shippableorder'] = Shippable_orders['頁面瀏覽數'].replace(',','')
                result['confirmed_sales_per_order_shippableorder'] = Shippable_orders['平均訂單金額'].replace(',','')
                result['cancelled_sales_shippableorder'] = Shippable_orders['不成立訂單的銷售額'].replace(',','')
                result['return_refund_orders_shippableorder'] = Shippable_orders['退貨/退款訂單'].replace(',','')
                result['return_refund_sales_shippableorder'] = Shippable_orders['退貨/退款的銷售額'].replace(',','')
                result['buyers_shippableorder'] = float(Shippable_orders['買家數'].astype(str).replace(',',''))
                result['new_buyers_shippableorder'] = float(Shippable_orders['新買家數'].astype(str).replace(',',''))
                result['existing_buyers_shippableorder'] = float(Shippable_orders['舊買家數'].astype(str).replace(',',''))
                result['potential_buyers_shippableorder'] = float(Shippable_orders['潛在買家數'].astype(str).replace(',',''))
                result['repeat_purchase_rate_shippableorder'] = float(Shippable_orders['回購率'].replace('%',''))
                all_orders = pd.read_excel(resp.content,sheet_name='全部訂單').iloc[0]
                result['confirmed_gmv_allorders'] = all_orders['總銷售額 (TWD)'].replace(',','')
                result['confirmed_orders_allorders'] = all_orders['訂單總數'].replace(',','')
                result['cancelled_orders_allorders'] = all_orders['不成立的訂單'].replace(',','')
                result['shop_uv_to_confirmed_buyers_rate_allorders'] = float(all_orders['下單轉換率'].replace('%',''))
                result['shop_uv_allorders'] = all_orders['訪客數'].replace(',','')
                result['shop_pv_allorders'] = all_orders['頁面瀏覽數'].replace(',','')
                result['confirmed_sales_per_order_allorders'] = all_orders['平均訂單金額'].replace(',','')
                result['cancelled_sales_allorders'] = all_orders['不成立訂單的銷售額'].replace(',','')
                result['return_refund_orders_allorders'] = all_orders['退貨/退款訂單'].replace(',','')
                result['return_refund_sales_allorders'] = all_orders['退貨/退款的銷售額'].replace(',','')
                result['buyers_allorders'] = float(all_orders['買家數'].astype(str).replace(',',''))
                result['new_buyers_allorders'] = float(all_orders['新買家數'].astype(str).replace(',',''))
                result['existing_buyers_allorders'] = float(all_orders['舊買家數'].astype(str).replace(',',''))
                result['potential_buyers_allorders'] = float(all_orders['潛在買家數'].astype(str).replace(',',''))
                result['repeat_purchase_rate_allorders'] = float(all_orders['回購率'].replace('%',''))
                                
                # 運用requests以及pandas 把EXCEL讀取出來
                url = f'https://seller.shopee.tw/api/mydata/v2/product/overview/export/?start_ts={y_start}&end_ts={y_end}&period=yesterday'
                resp = session.get(url)
                if resp.status_code != 200:
                    logger.info('\n' + traceback.format_exc())
                    return {'success':False, 'message':'讀取EXCEL失敗:商品', 'data':{}}
                
                df = pd.read_excel(resp.content)
                result['uv'] = df['商品頁的訪客數'].sum()
                result['pv'] = df['商品頁瀏覽數'].sum()
                result['iv'] = df['被瀏覽商品數'].sum()
                result['bounce_rate'] = df['商品頁的跳出率'].str.replace('%', '').astype(float).mean()
                result['like_unit_num'] = df['商品按讚數'].sum()
                result['atc_unit_num'] = df['加入購物車(件數)'].sum()
                result['atc_uv'] = df['商品頁訪客數(加入購物車)'].sum()
                result['atc_rate'] = df['加入購物車轉換率'].str.replace('%', '').astype(float).mean()
                result['placed_unit_num'] = df['訂單商品件數(可出貨訂單)'].sum()
                result['confirmed_gmv'] = df['銷售額(可出貨訂單) (TWD)'].astype(str).str.replace(',','').astype(int).sum()
                result['placed_buyers'] = df['可出貨商品數量'].sum()
                result['uv_to_confirmed_buyers_rate'] = df['轉換率 (可出貨訂單除以不重複訪客數)'].str.replace('%', '').astype(float).mean()
                result['UpdateDate'] = UpdateDate
                result['LogDate'] = LogDate
                self.driver.get('https://seller.shopee.tw/')
                return {'success':True, 'message':'', 'data':result}
            except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException,):
                error_count += 1
                # 判斷是否有跳出訊息
                result_window = self.popup_window()
                if (result_window['success'] and result_window['message']) or result_window['success'] is False:
                    logger.info(result_window['message'])
                if result_window['success'] and not result_window['message']:
                    logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                time.sleep(1)
                self.driver.get('https://seller.shopee.tw/')
                continue
            except NoSuchElementException:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生NoSuch可能改版, 請確認原因')
                return {'success':False, 'message':'發生NoSuch可能改版, 請確認原因', 'data':[]}
            except (WebDriverException, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                error_count += 1
                logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(3)
                continue
            except Exception:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生未知異常, 請確認原因')
                return {'success':False, 'message':'發生未知異常, 請確認原因', 'data':[]}
    # 爬取賣家數據中心 > 賣家表現
    def Product_Performance(self, store):
        error_count = 0
        while True:
            try:
                # 判斷回到主頁
                WebDriverWait(self.driver, 10, 2).until(EC.presence_of_element_located((By.CLASS_NAME,'sidebar-submenu-item-link')))
                self.driver.get('https://seller.shopee.tw/datacenter/dashboard')
                # 判斷是否在賣家中心
                WebDriverWait(self.driver, 10, 2).until(EC.presence_of_element_located((By.CLASS_NAME,'bi-date-input.track-click-open-time-selector')))
                # 切換到商品
                self.driver.find_element_by_css_selector('a.nav-tab.datacenter-products').click()
                # 點擊商品表現
                WebDriverWait(self.driver, 10, 2).until(EC.presence_of_element_located((By.CLASS_NAME,'side-navbar-item')))
                html = requests_html.HTML(html=self.driver.page_source)
                performance_count = None
                for i,soup in enumerate(html.find('li.side-navbar-item')):
                    if soup.text.split('\n')[0] == '商品表現':
                        performance_count = i+1
                element = self.driver.find_element(by=By.CSS_SELECTOR, value=f'li.side-navbar-item:nth-child({performance_count})')
                ActionChains(self.driver).click(element).perform()
                # 點擊資料期間
                WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'bi-date-input.track-click-open-time-selector')))
                element = self.driver.find_element_by_css_selector('div.bi-date-input.track-click-open-time-selector')
                ActionChains(self.driver).click(element).perform()
                # 點擊昨日
                WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,f'shopee-date-shortcut-item.track-click-time-selector.edu-date-picker-option')))
                count = 0
                html = requests_html.HTML(html=self.driver.page_source)
                for i, key in enumerate(html.find('li.shopee-date-shortcut-item.track-click-time-selector.edu-date-picker-option')):
                    if '昨日' in key.text:
                        count = i+1
                        break
                WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'li.shopee-date-shortcut-item.track-click-time-selector.edu-date-picker-option:nth-child({count})')))
                #self.driver.find_element_by_css_selector(f'li.shopee-date-shortcut-item.track-click-time-selector.edu-date-picker-option:nth-child({count})').click()
                element = self.driver.find_element(by=By.CSS_SELECTOR, value=f'li.shopee-date-shortcut-item.track-click-time-selector.edu-date-picker-option:nth-child({count}) > span.shopee-date-shortcut-item__text')
                ActionChains(self.driver).click(element).perform()
                # 點擊商品表現 > 匯出報表
                WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'export.shopee-button.shopee-button--normal')))
                element = self.driver.find_element(by=By.CSS_SELECTOR, value='button.export.shopee-button.shopee-button--normal')
                ActionChains(self.driver).click(element).perform()
                time.sleep(1)
                # 點擊商品表現 > 匯出報表 > 下載
                WebDriverWait(self.driver, 120, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.shopee-table__row.valign-top:nth-child(1) > td.is-last > div > div > button.shopee-button.shopee-button--primary.shopee-button--normal > span')))
                #time.sleep(10)
                element = self.driver.find_element(by=By.CSS_SELECTOR, value='tr.shopee-table__row.valign-top > td.is-last > div > div > button.shopee-button.shopee-button--primary.shopee-button--normal')
                ActionChains(self.driver).click(element).perform()
                # 取出檔案資料
                excel_count = 0
                while True:
                    excel_path = [Path('.', str(i)) for i in path.iterdir() if 'export' in str(i)]
                    excel_path = excel_path[0] if excel_path else None
                    if excel_path:
                        logger.info('EXCEL檔案捕捉完成')
                        break
                    else:
                        logger.info('EXCEL下載未完成, 2秒後重試捕捉')
                        time.sleep(2)
                        continue
                        #return {'success':False, 'message':f'下載EXCEL後, 查無EXCEL檔案, 資料夾內容:{path.iterdir()}', 'data':[]}
                df = pd.read_excel(str(excel_path.absolute()))
                recode = df.to_dict('record')
                data_group = [list(j) for i,j in groupby(sorted(recode, key=lambda x:x['商品ID']), key=lambda x:x['商品ID'])]
                # result的檔案時間
                yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
                up_dt = datetime.datetime.now()
                log_dt = datetime.datetime.now().replace(minute=0, second=0,microsecond=0)
                UpdateDate = up_dt.strftime('%Y-%m-%d %H:%M:%S')
                LogDate = log_dt.strftime('%Y-%m-%d %H:%M:%S')
                # 開始資料捕捉
                result = []
                for datas in data_group:
                    main_information = {}
                    secondary_information = []
                    products = {}
                    for data in datas:
                        if data['商品規格'] == '-':
                            main_information = dict(
                                                    uv = data['商品頁的訪客數'],
                                                    pv = data['商品頁瀏覽數'],
                                                    bounce_rate = data['商品頁的跳出率'],
                                                    like_unit_num = data['商品按讚數'],
                                                    atc_rate = data['加入購物車轉換率'],
                                                    shop_uv_allorders_rate = data['轉換率 (全部訂單除以不重複訪客數)'],
                                                    uv_to_confirmed_buyers_rate = data['轉換率 (可出貨訂單除以不重複訪客數)'],
                                                    uv_to_paid_order_rate = data['轉換率 (已付款訂單除以不重複訪客數)']
                                                )
                        else:
                            secondary_information.append(data)
                    for data in secondary_information:
                        products['shopid'] = store
                        products['TargetDate'] = yesterday
                        products['product_name'] = data['商品名稱']
                        products['platformproduct_phopeeid'] = str(data['商品ID'])
                        products['product_specification'] = data['商品規格']
                        products['product_specification_id'] = data['商品規格ID']
                        products['platformid'] = data['商品選項貨號'] if data['商品選項貨號'] and data['商品選項貨號'] != '-' else data['主商品貨號']
                        products['uv'] = int(main_information['uv'].replace(',',''))
                        products['pv'] = int(main_information['pv'].replace(',',''))
                        products['bounce_rate'] = float(main_information['bounce_rate'].replace('%',''))
                        products['like_unit_num'] = int(main_information['like_unit_num'].replace(',',''))
                        products['atc_uv'] = int(data['商品頁訪客數(加入購物車)'])
                        products['atc_unit_num'] = int(data['加入購物車(件數)'])
                        products['atc_rate'] = float(main_information['atc_rate'].replace('%', ''))
                        products['shop_buyers_allorders'] = int(data['不重複買家數(全部訂單)'])
                        products['confirmed_orders_num'] = int(data['下單商品件數'])
                        products['confirmed_gmv'] = data['下單金額 (TWD)'] if type(data['下單金額 (TWD)']) == int else int(data['下單金額 (TWD)'].replace(',', ''))
                        products['shop_uv_allorders_rate'] = float(main_information['shop_uv_allorders_rate'].replace('%', ''))
                        products['shop_buyers_shippableorder'] = int(data['不重複買家數(可出貨訂單)'])
                        products['placed_unit_num'] = int(data['訂單商品件數(可出貨訂單)'])
                        products['confirmed_gmv_shippableorder'] = data['銷售額(可出貨訂單) (TWD)'] if type(data['銷售額(可出貨訂單) (TWD)']) == int else int(data['銷售額(可出貨訂單) (TWD)'].replace(',',''))
                        products['uv_to_confirmed_buyers_rate'] = float(main_information['uv_to_confirmed_buyers_rate'].replace('%', ''))
                        products['allorders_to_shippableorder_rate'] = float(data['全部訂單到可出貨訂單轉換率'].replace('%',''))
                        products['shop_buyers_paid_order'] = int(data['不重複買家(付款訂單)'])
                        products['paid_num'] = int(data['付款件數'])
                        products['payment_amount'] = data['付款金額 (TWD)'] if type(data['付款金額 (TWD)']) == int else int(data['付款金額 (TWD)'].replace(',',''))
                        products['uv_to_paid_order_rate'] = float(main_information['uv_to_paid_order_rate'].replace('%',''))
                        products['UpdateDate'] = UpdateDate
                        products['LogDate'] = LogDate
                        result.append(products)
                # 刪除檔案
                excel_path.unlink()
                # 回傳資訊
                self.driver.get('https://seller.shopee.tw/')
                return {'success':True, 'message':'', 'data':result}
            except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException,):
                error_count += 1
                if error_count > 5:
                    return {'success':False, 'message':'重試超過5次, 請人工確認', 'data':[]}
                # 判斷是否有跳出訊息
                result_window = self.popup_window()
                if (result_window['success'] and result_window['message']) or result_window['success'] is False:
                    logger.info(result_window['message'])
                if result_window['success'] and not result_window['message']:
                    logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                time.sleep(1)
                self.driver.get('https://seller.shopee.tw/')
                continue
            except NoSuchElementException:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生NoSuch可能改版, 請確認原因')
                return {'success':False, 'message':'發生NoSuch可能改版, 請確認原因', 'data':[]}
            except (WebDriverException, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                error_count += 1
                logger.info('\n' + traceback.format_exc())
                logger.info(f'進行重試:{error_count}')
                self.driver.get('https://seller.shopee.tw/')
                time.sleep(3)
                continue
            except Exception:
                logger.info('\n' + traceback.format_exc())
                logger.info('發生未知異常, 請確認原因')
                return {'success':False, 'message':'發生未知異常, 請確認原因', 'data':[]}
    # 判斷是否有跳出訊息
    def popup_window(self):
        try:
            #WebDriverWait(self.driver, 3)
            #WebDriverWait(self.driver, 5, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'shopee-modal.new-look-step0')))
            if '請再次輸入登入密碼以進行下一步' in self.driver.page_source:
                input_pw = self.driver.find_element(by=By.CSS_SELECTOR, value='input.shopee-input__input')
                input_pw.send_keys(self.pwd)
                # 點擊確認
                enter = self.driver.find_element(by=By.CSS_SELECTOR, value='button.ios-action.shopee-button.shopee-button--primary.shopee-button--normal')
                enter.click()
                return {'success':True, 'message':'再次輸入帳密完成'}
            if '賣家數據中心已更新' in self.driver.page_source:
                enter = self.driver.find_element(by=By.CSS_SELECTOR, value='div.shopee-modal.new-look-step0 > div > div > div > div > div.shopee-modal__footer > div.shopee-modal__footer-buttons > button.shopee-button.shopee-button--primary.shopee-button--normal')
                ActionChains(self.driver).click(enter).perform()
                WebDriverWait(self.driver, 5, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME,'edu-dialog_title')))
                enter = self.driver.find_element(by=By.CSS_SELECTOR, value='button.shopee-button.shopee-button--small:not(.shopee-button--primary)')
                ActionChains(self.driver).click(enter).perform()
                return {'success':True, 'message':'點擊賣家數據中心完成'}
            if 'shopee-modal dashboard-notice-shopee-modal' in self.driver.page_source:
                element = self.driver.find_element(by=By.CSS_SELECTOR, value='div.shopee-modal.dashboard-notice-shopee-modal > div > div > div > div > div.shopee-modal__footer > div')
                ActionChains(self.driver).click(element).perform()
                {'success':True, 'message':'點擊操作說明完成'}
            return {'success':True, 'message':''}
        except:
            return {'success':False, 'message':f'跳出訊息處理失敗:\n{traceback.format_exc()}'}
    # 取出cookies
    def get_cookies(self):
        cookies = self.driver.get_cookies()
        return cookies
    # 關閉爬蟲
    def driver_close(self):
        self.driver.close()
        return

            
        
    

