## Utilizing LLM and Amazon Bedrock Agents for Stock Analysis
The aim of this project is to develop an automated system for comprehensive stock analysis utilizing balance sheet data, technical indicators, and news, powered by large language models (LLMs) such as Claude 3, and leveraging AWS Bedrock infrastructure.

**Stock Analyst Module**

- Conducts automated stock analysis weekly.
- Integrates balance sheet information, technical indicators, and relevant news.
- Utilizes LLMs to rank stocks within their respective industries.
- Generates BUY/SELL recommendations for each stock based on the analysis.
- Analytics results are stored in a database for further analytics and trend tracking.

**Portfolio Manager Module**

- Weekly updates to the portfolio with new stocks based on the stock analyst's recommendations + general market sentiment.
- Allows user prompts to influence the selection and weighting of stocks in the portfolio.

### Architecture Overview

![Architecture](documentation/architecture.png)

Following outlines the process flow for a stock analysis application leveraging various AWS services and external APIs. The key components and steps involved are as follows:

**Stock Analyst**

1. The process is triggered by an event scheduled with AWS EventBridge.
2. The event initiates a task within the AWS Elastic Container Service (ECS), which fetches earning reports from the Yahoo Finance API.
3. A prompt is sent to an Amazon Bedrock Agent which performs web searches, and summarizes key data points and relevant news for each stock. 
   - The Action Group component combines the instructions, the prompt engineering, and the relevant data from various sources. 
   - AWS Lambda functions are utilized for web scraping from public websites and to retrieve google search results.
4. The Amazon Bedrock Claude service summarizes the news and relevant data gathered. News from different websites are aggregated and summarized by the LLM.
5. Earning reports, news and industry benchmarks are send to Amazon Bedrock Claude to rank stocks within their industries.
6. The LLM's recommendation, along with the summarized data, is saved in an Amazon DynamoDB database.

**Portfolio Manager**

7. The process is triggered by an event scheduled with AWS EventBridge.
8. A day a prompt is sent to an Amazon Bedrock Agent to collect generic market news.
9. The LLM acts as a portfolio manager with the information the analyst provided and changes the portfolio. 

### Getting Started

```
cd infrastructure
cdk deploy
```
- After the infrastructure is deplyoed you have to run the python script `infrastructure/deploy_agents.py` because currently AWS CDK does nor support Amazon Bedrock Agents.
Change the variables in the python script with values created by the CDK stack. After the script is deployed go to the Amazon Bedrock agent console.

- Go to the Amazon Bedrock Agent console and follow the steps below to setup the Action groups. This is currently not supported by any API or IaC.
- Click on `Agents`->`InternetSearchAgent`->`Edit in Agent Builder`->`Additional settings`-> Enable User Input
- Click on `Add Action Group`
  - Enter Action group name `InternetSearch`
  - `Description`: this action group is use to google specific inputs 
  - Select the existing Lambda function created with CDK.
  - `Define inline schema` and copy the content from `src/schema/internet-search-schema.json`
  - Save end exit

- Click edit agent. Go to advanced prompts settings. Toggle on the **Override pre-processing template defaults** radio button. Also make sure the **Activate pre-processing template** radio button is enabled.
- Under *prompt template editor*, you will notice that you now have access to control the pre-built prompts. Scroll down to until you see "Category D". Replace this category section with the following:

   ```text
  -Category D: Questions that can be answered by internet search, or assisted by our function calling agent using ONLY the functions it has been provided or arguments from within <conversation_history> or relevant arguments it can gather using the askuser function.
   ```

- After, scroll down and select **Save & Exit**.

Test the agent with some sample prompts:

```text
- Q1: Do an internet search and summarize news about Merck which can influence the stock price
- Q2: Do an internet search and summarize news about Ticketmaster which can influence the stock price
  ```
  
As a last step you need to manually update the AgentId and Alias in the code used to get daily news for each stock:
- Go to `src/helper/advisor.py` and update in line `176` and `177` the values with the model id and alias form the previously steps.

### Results

For results see `documentation/RESULTS.md`

### Prompt Engineering

To improve the performance and behaviour of the models you can change the prompts in the file `src/schema/prompts.yaml`.

### Financial data collected for each stock

Financial Performance Metrics

    Previous Close
    Open
    Day Low
    Day High
    Regular Market Previous Close
    Regular Market Open
    Regular Market Day Low
    Regular Market Day High
    Dividend Rate
    Dividend Yield
    Trailing PE
    Forward PE
    Volume
    Regular Market Volume
    Average Volume
    Average Volume 10 days
    Average Daily Volume 10 Day
    Market Cap
    Fifty-Two Week Low
    Fifty-Two Week High
    Price to Sales Trailing 12 Months
    Fifty-Day Average
    Two-Hundred-Day Average
    Trailing Annual Dividend Rate
    Trailing Annual Dividend Yield
    Beta
    Profit Margins
    Float Shares
    Shares Outstanding
    Shares Short
    Shares Short Prior Month
    Shares Short Previous Month Date
    Date Short Interest
    Shares Percent Shares Out
    Held Percent Insiders
    Held Percent Institutions
    Short Ratio
    Short Percent Of Float
    Book Value
    Price to Book
    Last Fiscal Year End
    Next Fiscal Year End
    Most Recent Quarter
    Earnings Quarterly Growth
    Net Income To Common
    Trailing EPS
    Forward EPS
    PEG Ratio
    Enterprise Value
    Enterprise to Revenue
    Enterprise to EBITDA
    Total Cash
    Total Cash Per Share
    EBITDA
    Total Debt
    Quick Ratio
    Current Ratio
    Total Revenue
    Debt to Equity
    Revenue Per Share
    Return On Assets
    Return On Equity
    Free Cashflow
    Operating Cashflow
    Earnings Growth
    Revenue Growth
    Gross Margins
    EBITDA Margins
    Operating Margins

Valuation and Market Position

    Currency
    Current Price
    Target High Price
    Target Low Price
    Target Mean Price
    Target Median Price
    Recommendation Mean
    Recommendation Key
    Number Of Analyst Opinions

Governance and Risk Factors

    Audit Risk
    Board Risk
    Compensation Risk
    Shareholder Rights Risk
    Overall Risk

Industry Comparison

    Industry Average Trailing PE
    Industry Average Forward PE
    Industry Average Average Volume
    Industry Average Trailing Annual Dividend Rate
    Industry Average Profit Margins
    Industry Average Short Ratio
    Industry Average Short Percent Of Float
    Industry Average Book Value
    Industry Average Trailing EPS
    Industry Average Forward EPS
    Industry Average EBITDA
    Industry Average Total Debt
    Industry Average Total Revenue
    Industry Average Debt To Equity
    Industry Average Free Cashflow
    Industry Average Earnings Growth
    Industry Average Revenue Growth
    Industry Average Operating Margins
    Industry Average PEG Ratio
    Industry Average Gross Margins
    Industry Average EBITDA Margins

Company Information

    Exchange
    Quote Type
    Symbol
    Short Name
    Long Name
    First Trade Date Epoch Utc
    Time Zone Full Name
    Time Zone Short Name
    Uuid
    Gmt Offset Milliseconds
    Financial Currency
    Stock News
    Rank
    Explanation
    Investment Decision
    Industry
    Date

Dates and Epochs

    Governance Epoch Date
    Compensation As Of Epoch Date
    Ex Dividend Date
    Last Split Date

News
    
    Recent news about the stock

### Improvements
- Portfolio management user prompt is very big and the performance lacks with long inputs (100s of stock info at once), split task into smaller subtasks
- Limit hallucination of models for more consistent results and break the problem into smaller subtasks

### Reference
- https://github.com/build-on-aws/bedrock-agents-webscraper
- https://bfi.uchicago.edu/wp-content/uploads/2024/05/BFI_WP_2024-65.pdf

### License

This project is licensed under the MIT License. Feel free to use and modify the code as needed.