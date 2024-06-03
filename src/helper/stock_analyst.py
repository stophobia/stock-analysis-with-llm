import yaml
from helper.helper import parse_response, retry, invoke_model, invoke_agent
from aws_lambda_powertools import Logger

logger = Logger()


class StockAnalyst:
    def __init__(self):
        with open('schema/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)

        self.prompts = prompts

    def stock_analysis(self, finance_api, database):
        logger.info('Start stock analytics')
        for industry, stocks in finance_api.industries.items():
            if len(stocks) < 4:
                continue

            self.compare_stocks_with_retry(stocks, industry, finance_api, database)

        logger.info('Finished stock analytics')

    def compare_stocks(self, stocks, industry, finance_api, database):
        data_per_symbol = []
        for symbol in stocks:
            data, ticker = finance_api.get_history(symbol['symbol'])

            self._add_industry_average_to_ticker(ticker, symbol['symbol'], finance_api)
            ticker.info['name'] = symbol['name']

            input_text = self.prompts['agent_web_search_stock_analyst']['prompt'].replace("<stock_name>",
                                                                                          symbol['name'])

            ticker.info['StockNews'] = invoke_agent(input_text)

            data_per_symbol.append(self._remove_unused_data_for_ai(ticker.info))

        stocks_to_send = self.get_ranking(data_per_symbol, industry, finance_api)

        for st in stocks_to_send:
            st['industry'] = industry
            st['date'] = str(finance_api.today.strftime('%Y-%m-%d'))

        database.save_stock_analytics(stocks_to_send)

    def get_ranking(self, data, industry, finance_api):

        # Prompt with user turn only.
        content = self.prompts['stock_analytics_user']['prompt'].replace("<data>", str(data))

        system_prompt = self.prompts['stock_analytics_system']['prompt'].replace('<date>',
                                                                                 str(finance_api.today.strftime(
                                                                                     '%Y-%m-%d'))) \
            .replace('<industry>', industry)

        response = invoke_model([{
            "role": "user",
            "content": content
        }], system_prompt)

        stock_indicators = data
        for ai_ranking in response:
            for stock_indicator in stock_indicators:
                if 'symbol' in ai_ranking and stock_indicator['symbol'] == ai_ranking['symbol']:

                    rank = ai_ranking.get('rank', 99)
                    explanation = ai_ranking.get('explanation', '')
                    investment_decision = ai_ranking.get('investment_decision', '')

                    if rank == 'null' or rank is None or rank == 'None' or rank == 'N/A':
                        rank = 99

                    stock_indicator["rank"] = rank
                    stock_indicator["explanation"] = explanation
                    stock_indicator["investment_decision"] = investment_decision

        try:
            stock_indicators_sorted = sorted(stock_indicators, key=lambda d: d.get('rank', 99))
        except Exception as e:
            logger.info(f'Error while sorting by rank, {e}')
            stock_indicators_sorted = stock_indicators

        return stock_indicators_sorted

    def _remove_unused_data_for_ai(self, data):
        parameters = ['address1', 'address2', 'city', 'state', 'zip', 'country',
                      'phone', 'phone', 'fax', 'website', 'industry',
                      'industryKey', 'industryKey', 'industryDisp', 'sector', 'sectorKey', 'sectorDisp',
                      'longBusinessSummary', 'fullTimeEmployees', 'companyOfficers']
        return {key: value for key, value in data.items() if key not in parameters}

    def _add_industry_average_to_ticker(self, ticker, symbol, finance_api):
        parameters = ["trailingPE", "forwardPE", "averageVolume", "trailingAnnualDividendRate", "profitMargins",
                      "shortRatio", "shortPercentOfFloat", "bookValue", "trailingEps", "forwardEps", "ebitda",
                      "totalDebt", "totalRevenue", "debtToEquity", "freeCashflow", "earningsGrowth",
                      "revenueGrowth", "operatingMargins", "pegRatio", "grossMargins", "ebitdaMargins"]

        for parameter in parameters:
            industry_avg = finance_api.get_industry_or_sector_data(symbol,
                                                                   name="industry",
                                                                   parameter=parameter)

            ticker.info[f"industryAverage{parameter[0].upper()}{parameter[1:]}"] = industry_avg

            symbol_val = finance_api.get_info(ticker, parameter=parameter)
            ticker.info[parameter] = symbol_val

    @retry(retries=3, delay=60 * 5)
    def compare_stocks_with_retry(self, stocks, industry, finance_api, database):
        self.compare_stocks(stocks, industry, finance_api, database)
