from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index, DateTime, Boolean, Table, MetaData, DECIMAL, column
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from sqlalchemy import and_, or_
import pymysql
from .config import load_setting, line
import logging
from ..logs import log
import traceback
logger = logging.getLogger('robot')

#取得資料
db_data = load_setting()
url_port = db_data['config']['db']['url_port']
acc = db_data['config']['db']['acc']
pw = db_data['config']['db']['pw']
db_name = db_data['config']['db']['db_name']

# 寫入MySQL
engine = create_engine(f'mysql+pymysql://{acc}:{pw}@{url_port}/{db_name}')
Base = declarative_base()
session = sessionmaker(bind=engine)
session = session()

# 製作資料表格式
class Data(Base):
    __tablename__ = 'Shopee_Seller_Data_Center_Traffic'
    shopid = Column(Integer, primary_key=True)
    TargetDate = Column(DateTime)
    confirmed_gmv_shippableorder = Column(Integer)
    confirmed_orders_shippableorder = Column(Integer)
    cancelled_orders_shippableorder = Column(Integer)
    shop_uv_to_confirmed_buyers_rate_shippableorder = Column(DECIMAL(5,2))
    shop_uv_shippableorder = Column(Integer)
    shop_pv_shippableorder = Column(Integer)
    confirmed_sales_per_order_shippableorder = Column(DECIMAL(10,2))
    cancelled_sales_shippableorder = Column(Integer)
    return_refund_orders_shippableorder = Column(Integer)
    return_refund_sales_shippableorder = Column(Integer)
    buyers_shippableorder= Column(DECIMAL(10,2))
    new_buyers_shippableorder = Column(DECIMAL(10,2))
    existing_buyers_shippableorder = Column(DECIMAL(10,2))
    potential_buyers_shippableorder = Column(DECIMAL(10,2))
    repeat_purchase_rate_shippableorder = Column(DECIMAL(5,2))
    confirmed_gmv_allorders = Column(Integer)
    confirmed_orders_allorders = Column(Integer)
    cancelled_orders_allorders = Column(Integer)
    shop_uv_to_confirmed_buyers_rate_allorders = Column(DECIMAL(5,2))
    shop_uv_allorders = Column(Integer)
    shop_pv_allorders = Column(Integer)
    confirmed_sales_per_order_allorders = Column(DECIMAL(10,2))
    cancelled_sales_allorders = Column(Integer)
    return_refund_orders_allorders = Column(Integer)
    return_refund_sales_allorders = Column(Integer)
    buyers_allorders = Column(DECIMAL(10,2))
    new_buyers_allorders = Column(DECIMAL(10,2))
    existing_buyers_allorders = Column(DECIMAL(10,2))
    potential_buyers_allorders = Column(DECIMAL(10,2))
    repeat_purchase_rate_allorders = Column(DECIMAL(5,2))
    uv = Column(Integer)
    pv = Column(Integer)
    iv = Column(Integer)
    bounce_rate = Column(DECIMAL(5,2))
    like_unit_num = Column(Integer)
    atc_unit_num = Column(Integer)
    atc_uv = Column(Integer)
    atc_rate = Column(DECIMAL(5,2))
    placed_unit_num = Column(Integer)
    confirmed_gmv = Column(Integer)
    placed_buyers = Column(Integer)
    uv_to_confirmed_buyers_rate = Column(DECIMAL(5,2))
    UpdateDate = Column(DateTime)
    LogDate = Column(DateTime)


#     __table_args__ = (
#     UniqueConstraint('id','fullname'),
#         Index('fullname')
#     )
    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
    # def __repr__(self):
    #     return f'【訂單編號】:{self.ORDERID},【產品名稱】:{self.PRODUCTNAME},【產品數量】:{self.QTY},【產品售價】:{self.PRICE}'

def create_all(data_list):
    try:
        session.add_all([Data(**data) for data in data_list])
        session.commit()
        logger.info('寫入db成功')
        return True
    except Exception:
        line(message=f"【蝦皮賣家中心】發生錯誤, 內容:【資料庫寫入發生錯誤】")
        logger.info('\n' + traceback.format_exc())
        logger.info('寫入db失敗')
        return False
