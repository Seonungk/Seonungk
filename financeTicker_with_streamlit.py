from dotenv import load_dotenv
load_dotenv("../.env")

import os
import requests
import json
import yfinance as yf
from yahooquery import Ticker
import openai
from openai import OpenAI  
client = OpenAI()

serpapi = os.environ["SERP_API_KEY"] 

def get_company_news(company_name):
    params = {
        "engine": "google",
        "tbm": "nws",
        "q": company_name,
        "api_key": os.environ["SERP_API_KEY"],
    }

    response = requests.get('https://serpapi.com/search', params=params)
    data = response.json()

    return data.get('news_results')


def write_news_to_file(news, filename):
    with open(filename, 'w') as file:
        for news_item in news:
            if news_item is not None:
                title = news_item.get('title', 'No title')
                link = news_item.get('link', 'No link')
                date = news_item.get('date', 'No date')
                file.write(f"Title: {title}\n")
                file.write(f"Link: {link}\n")
                file.write(f"Date: {date}\n\n")


# company_name = "Microsoft"
# news = get_company_news(company_name)
# if news:
#     write_news_to_file(news, "investment.txt")
# else:
#     print("No news found.")


def get_stock_evolution(company_name, period="1y"):
    # Get the stock information
    stock = yf.Ticker(company_name)

    # Get historical market data
    hist = stock.history(period=period)

    # Convert the DataFrame to a string with a specific format
    data_string = hist.to_string()

    # Append the string to the "investment.txt" file
    with open("investment.txt", "a") as file:
        file.write(f"\nStock Evolution for {company_name}:\n")
        file.write(data_string)
        file.write("\n")
    return hist        

# get_stock_evolution("MSFT")  # replace "MSFT" with the ticker symbol of the company you are interested in


def get_financial_statements(ticker):
    # Create a Ticker object
    company = Ticker(ticker)

    # Get financial data
    try: 
        balance_sheet = company.balance_sheet().to_string()
    except: 
        balance_sheet = None 
    try:                
        cash_flow = company.cash_flow(trailing=False).to_string()
    except: 
        balance_sheet = None 
    try: 
        income_statement = company.income_statement().to_string()
    except: 
        balance_sheet = None 
    try: 
        valuation_measures = str(company.valuation_measures)  # This one might already be a dictionary or string
    except: 
        balance_sheet = None 


    # Write data to file
    with open("investment.txt", "a") as file:
        file.write("\nBalance Sheet\n")
        file.write(balance_sheet)
        file.write("\nCash Flow\n")
        file.write(cash_flow)
        file.write("\nIncome Statement\n")
        file.write(income_statement)
        file.write("\nValuation Measures\n")
        file.write(valuation_measures)

def get_data(company_name, company_ticker, period="1y", filename="investment.txt"):
    news = get_company_news(company_name)
    if news:
        write_news_to_file(news, filename)
    else:
        print("No news found.")

    hist = get_stock_evolution(company_ticker)

    get_financial_statements(company_ticker)        
    return hist

def financial_analyst(request):
    print(f"Received request: {request}")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role":
            "user",
            "content":
            f"Given the user request, what is the comapany name and the company stock ticker ?: {request}?"
        }],
        functions=[{
            "name": "get_data",
            "description":
            "Get financial data on a specific company for investment purposes",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type":
                        "string",
                        "description":
                        "The name of the company",
                    },
                    "company_ticker": {
                        "type":
                        "string",
                        "description":
                        "the ticker of the stock of the company"
                    },
                    "period": {
                        "type": "string",
                        "description": "The period of analysis"
                    },
                    "filename": {
                        "type": "string",
                        "description": "the filename to store data"
                    }
                },
                "required": ["company_name", "company_ticker"],
            },
        }],
        function_call={"name": "get_data"},
    )

    message = response.choices[0].message

    if message.function_call:
        # Parse the arguments from a JSON string to a Python dictionary
        arguments = json.loads(message.function_call.arguments)
        company_name = arguments["company_name"]
        company_ticker = arguments["company_ticker"]

        # Parse the return value from a JSON string to a Python dictionary
        hist = get_data(company_name, company_ticker)

        with open("investment.txt", "r") as file:
            content = file.read()[:14000]

        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "user",
                    "content": request
                },
                message,
                {
                    "role": "system",
                    "content": """write a detailled investment thesis to answer
                      the user request. Provide numbers to justify
                      your assertions, a lot ideally. Never mention
                      something like this:
                      However, it is essential to consider your own risk
                      tolerance, financial goals, and time horizon before
                      making any investment decisions. It is recommended
                      to consult with a financial advisor or do further
                      research to gain more insights into the company's f
                      undamentals and market trends. The user
                      already knows that"""
                },
                {
                    "role": "assistant",
                    "content": content,
                },
            ],
        )

        return second_response.choices[0].message.content, hist


# while True:
#     user_question = input("Enter your investment request:\n\n")

#     if user_question == 'exit':
#         break

#     print(financial_analyst(user_question))    

import streamlit as st 
import matplotlib.pyplot as plt 

def main(): 
    st.title("AI Financial Analyst App")

    company_name = st.text_input("Enter the company name: ")
    analyze_button = st.button("Analyze")

    if analyze_button:
        if company_name: 
            st.write("Analyzing.... please wait")
            investment_research, hist = financial_analyst(company_name)

            hist_selected = hist[['Open', "Close"]]

            # create figure 
            fig, ax = plt.subplots() 

            # plot the data
            hist_selected.plot(kind="line", ax=ax)

            # set title and labels
            ax.set_title(f"{company_name} Stock price")
            ax.set_xlabel("Date")
            ax.set_ylabel("Stock price")

            # display the plot
            st.pyplot(fig)
            st.write("Investment Research / Recommendation:")
            st.markdown(investment_research, unsafe_allow_html=True)

            st.write("Enter the company name")


if __name__ == "__main__": 
    main()