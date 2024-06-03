from helper.helper import get_stocks, invoke_agent, invoke_model
import yaml

from aws_lambda_powertools import Logger

logger = Logger()


class PortfolioManager:
    def __init__(self):
        with open('schema/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)

        self.prompts = prompts

    def manage_portfolio(self, finance_api, database):
        date = str(finance_api.today.strftime('%Y-%m-%d'))
        logger.info(f'Start portfolio manager {date}')

        stocks = get_stocks(finance_api)
        logger.info(f'{len(stocks)} stocks found')

        market_sentiment = ''
        try:
            market_sentiment += invoke_agent(self.prompts['agent_web_search_portfolio_manger']['prompt'].
                                             replace("<term>", "US")) + "; "
            market_sentiment += invoke_agent(self.prompts['agent_web_search_portfolio_manger']['prompt'].
                                             replace("<term>", "EU")) + "; "
            market_sentiment += invoke_agent(self.prompts['agent_web_search_portfolio_manger']['prompt'].
                                             replace("<term>", "Chine"))
        except Exception as e:
            logger.info(f'Error getting market sentiment, error: {e}')

        stock_analysis = database.get_analyst_data(stocks=stocks, date=date)
        logger.info(f'{len(stock_analysis)} stocks analysis found from today {date}')
        for stock in stock_analysis:
            try:
                del stock['stock_news']
            except:
                continue

        content = self.prompts['portfolio_manager_user']['prompt'].replace("<data>", str({"general_market_sentiment":
                                                                                              market_sentiment,
                                                                                          "stocks":
                                                                                              stock_analysis}))
        system_prompt = self.prompts['portfolio_manager_system']['prompt']
        response = invoke_model([{
            "role": "user",
            "content": content
        }], system_prompt)

        logger.info(f'Response: {response}')
        database.save_portfolio(response, date)
        logger.info(f'Finished portfolio manager')
