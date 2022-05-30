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
    __tablename__ = 'Shopee_Seller_Data_Center_Performance'
    shopid = Column(Integer, primary_key=True)
    TargetDate = Column(DateTime)
    product_name = Column(String)
    platformproduct_phopeeid = Column(String)
    product_specification = Column(String)
    product_specification_id = Column(String)
    platformid = Column(String)
    uv = Column(Integer)
    pv = Column(Integer)
    bounce_rate = Column(DECIMAL(5,2))
    like_unit_num = Column(Integer)
    atc_uv = Column(Integer)
    atc_unit_num = Column(Integer)
    atc_rate = Column(DECIMAL(5,2))
    shop_buyers_allorders = Column(Integer)
    confirmed_orders_num = Column(Integer)
    confirmed_gmv = Column(Integer)
    shop_uv_allorders_rate = Column(DECIMAL(5,2))
    shop_buyers_shippableorder = Column(Integer)
    placed_unit_num = Column(Integer)
    confirmed_gmv_shippableorder = Column(Integer)
    uv_to_confirmed_buyers_rate = Column(DECIMAL(5,2))
    allorders_to_shippableorder_rate = Column(DECIMAL(5,2))
    shop_buyers_paid_order = Column(Integer)
    paid_num = Column(Integer)
    payment_amount = Column(Integer)
    uv_to_paid_order_rate = Column(DECIMAL(5,2))
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
        logger.info('寫入db中..')
        session.add_all([Data(**data) for data in data_list])
        session.commit()
        logger.info('寫入db成功')
        return True
    except Exception:
        line(message=f"【蝦皮賣家中心】發生錯誤, 內容:【資料庫寫入發生錯誤】")
        logger.info('\n' + traceback.format_exc())
        logger.info('寫入db失敗')
        return False
