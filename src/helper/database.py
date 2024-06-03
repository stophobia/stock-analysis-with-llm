from dataclasses import dataclass

from aws_lambda_powertools import Logger
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
import os
import json

logger = Logger()

TABLE_NAME_STOCK_ANALYTICS = os.getenv("TABLE_NAME_STOCK_ANALYTICS", "StockAnalytics")
REGION = os.getenv("REGION", "eu-central-1")
TABLE_NAME_PORTFOLIO = os.getenv("TABLE_NAME_PORTFOLIO", "Portfolio")


class StockAnalysis(Model):
    class Meta:
        table_name = TABLE_NAME_STOCK_ANALYTICS
        region = REGION

    stock = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute(range_key=True)
    close = NumberAttribute()
    name = UnicodeAttribute(null=True)
    rank = NumberAttribute(null=True)
    stock_news = UnicodeAttribute(null=True)
    investment_decision = UnicodeAttribute(null=True)
    explanation = UnicodeAttribute(null=True)
    industry = UnicodeAttribute(null=True)


class Portfolio(Model):
    class Meta:
        table_name = TABLE_NAME_PORTFOLIO
        region = REGION

    stock = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute(range_key=True)
    name = UnicodeAttribute()
    number_of_shares_to_buy = NumberAttribute()


@dataclass()
class DatabaseService:

    def save_stock_analytics(self, objects):
        for obj in objects:
            try:
                item = StockAnalysis(stock=obj["symbol"],
                                     date=obj["date"],
                                     close=obj["previousClose"],
                                     rank=obj.get('rank', 999),
                                     stock_news=obj.get("StockNews", "None"),
                                     investment_decision=obj.get("investment_decision", "None"),
                                     explanation=obj.get("explanation", 'No explanation found'),
                                     industry=obj["industry"],
                                     name=obj.get('name'))
                item.save()
            except Exception as e:
                logger.info(f'Error while saving, obj : {obj}, error: {e}')

    def save_portfolio(self, objects, date):
        for obj in objects:
            try:
                item = Portfolio(stock=obj["symbol"],
                                 date=date,
                                 name=obj["name"],
                                 number_of_shares_to_buy=obj["number_of_shares_to_buy"])
                item.save()
            except Exception as e:
                logger.info(f'Error while saving, obj : {obj}, error: {e}')

    def get_analyst_data(self, stocks, date):
        item_keys = [(stock['symbol'], date) for stock in stocks]
        return [json.loads(item.to_json()) for item in StockAnalysis.batch_get(item_keys)]

    def get_portfolio_data(self):
        return [json.loads(item.to_json()) for item in self.scan(Portfolio)]

    def scan(self, model_class):
        rows = model_class.scan()
        return rows

    def delete_portfolio(self):
        portfolio = self.scan(Portfolio)
        with Portfolio.batch_write() as batch:
            for r in portfolio:
                batch.delete(r)
