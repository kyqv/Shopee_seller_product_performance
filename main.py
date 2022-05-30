
from lib.platfroms.mission import Shopee
from lib.config import config, db
from lib.logs import log
import logging
from dotenv import load_dotenv
import os
load_dotenv(override=True)

logger = logging.getLogger('robot')

def main():
    logger.info(f"版本號:{os.getenv('VERSION')}")
    # 讀取config.yaml
    config_yaml = config.load_setting()

    # 執行爬蟲
    shopee = Shopee.mission(
                            user=config_yaml['config']['user'], 
                            pwd=config_yaml['config']['pwd'], 
                            headless=config_yaml['config']['headless'], 
                            cookies=config_yaml['config']['cookies']
                            )
    result = shopee.robot()
    if not result['success']:
        config.line(message=f"發生錯誤!!!!{result['message']}")

    logger.info(f"一共獲取:{len(result['data'])}個商品數據")
    logger.info(f"數據資訊:{result['data'][0] if result['data'] else result['data']}")
    # 回存cookies至config.yaml
    config_yaml['config']['cookies'] = result['cookies']
    config.save_setting(data=config_yaml)
    logger.info('回存cookies成功')

    # 存入mysql
    if not config_yaml['config']['is_test'] and result['success']:    
        db_result = db.create_all(result['data'])
        if not db_result:
            logger.info('寫入DB失敗')
            return {'success':db_result, 'message':'寫入DB失敗'}
        # 結束任務
        logger.info('任務結束, 寫入DB成功')
        return {'success':db_result, 'message':'寫入DB成功'}

    else:
        logger.info('任務完成, 測試環境或任務失敗不需寫入DB')
        return {'seccess':result['success'],'message':'任務完成'}
    
if '__main__' == __name__:
    main()