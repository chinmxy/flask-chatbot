from flask import Flask, request, make_response, jsonify
import time
import datetime
from nsetools import Nse
from pprint import pprint
import json 
from newsapi import NewsApiClient
import random



app = Flask(__name__)

@app.route('/')
def index():
    return 'Server is running is at port 8000' 

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    nse = Nse() 
    with open('symbols.json') as json_file: 
        symbol_data = json.load(json_file)
    with open('inv_symbols.json') as json_file: 
        inv_symbol_data = json.load(json_file)
    newsapi = NewsApiClient(api_key='cc0446450bcc4e46a91abd02e33d5f85')
    
    req = request.get_json(silent=True, force=True)
    query_result = req.get('queryResult')

    if query_result.get('action') == 'get_stock_price':
        # query_result = req.get('queryResult')
        price_type = query_result.get('parameters').get('price_type')
        company_name = query_result.get('parameters').get('company_name')
        date_time = query_result.get('parameters').get('date-time')
        if isinstance(date_time, str):
            s = date_time.split("T")[0]
            unix_time = int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple()))
        else:
            s = date_time['date_time'].split("T")[0]
            unix_time = int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())) 
        start_date = unix_time
        end_date = unix_time + 86399
        try:
            company_symbol = symbol_data[company_name]
        except:
            return {
                "fulfillmentText": "Sorry! You need to enter a NSE belonging company.",
                "displayText": '25',
                "source": "webhookdata"
            }       
        q = nse.get_quote(company_symbol)
        prices = {"opening":q['open'], "closing":q['lastPrice'], "high":q['dayHigh'], "low":q['dayLow']}
        human_readable_date = datetime.datetime.utcfromtimestamp(unix_time).strftime("%d %B, %Y")
        op_string = "The {} price of {} on {} was Rs.{}.".format(price_type, company_name, human_readable_date, prices[price_type]) 

        return {
            "fulfillmentText": op_string,
            "displayText": '25',
            "source": "webhookdata"
        }
    elif query_result.get('action') == 'get_gainer':
        gainer_type = query_result.get('parameters').get('gainer_type')
        if query_result.get('parameters').get('number') == '':
            number = 1
        else:
            number = int(query_result.get('parameters').get('number'))
        top_gainers = nse.get_top_gainers()
        top_losers = nse.get_top_losers()
        
        if gainer_type == 'gainer':
            if number == 1:
                c_name = inv_symbol_data[top_gainers[0].get('symbol')]
                op_string = "The top gainer for the last trading session is {}.".format(c_name)
            else:
                company_list = []
                for i in range(number-1):
                    company_list.append(inv_symbol_data[top_gainers[i].get('symbol')])
                company_string = ", ".join(company_list)
                company_string += " and {}".format(inv_symbol_data[top_gainers[number-1].get('symbol')])
                op_string = "The top {} {}s are {}.".format(number, gainer_type, company_string)
        else:
            if number == 1:
                c_name = inv_symbol_data[top_losers[0].get('symbol')]
                op_string = "The top loser for the last trading session is {}.".format(c_name)
            else:
                company_list = []
                for i in range(number-1):
                    company_list.append(inv_symbol_data[top_losers[i].get('symbol')])
                company_string = ", ".join(company_list)
                company_string += " and {}".format(inv_symbol_data[top_losers[number-1].get('symbol')])
                op_string = "The top {} {}s are {}.".format(number, gainer_type, company_string)


        

        return {
            "fulfillmentText": op_string,
            "displayText": '25',
            "source": "webhookdata"
        }
    
    elif query_result.get('action') == 'get_news':
        company_name = query_result.get('parameters').get('company_name')
        all_articles = newsapi.get_everything(qintitle=company_name, sources='bbc-news,the-verge,the-times-of-india',language='en', sort_by='relevancy')
        articles = all_articles.get('articles')
        if len(articles) == 0:
            return {
            "fulfillmentText": "Sorry! Could not find any relevant news.",
            "displayText": '25',
            "source": "webhookdata"
            }
        article = articles[random.randint(0, len(articles)-1)]
        # pprint(article)
        title = article.get('title')
        url = article.get('url')
        url_img = article.get('urlToImage')
        subtitle = article.get('description')

        response = [{
                    "card":{
                    "title": title,
                    "subtitle": subtitle,
                    "imageUri":url_img,
                    "buttons":[
                    {
                    "text":"Read Full Story",
                    "postback":url
                    },
                    {
                    "text":"Get more news",
                    "postback": "Get more news for {}".format(company_name)
                    }
                    ]
                    },
                    "platform":"FACEBOOK"
                    }]
        
        return jsonify({
            "fulfillmentMessages": response
        })
    
    elif query_result.get('action') == 'get_index_quote':
        index_code = query_result.get('parameters').get('index_codes')
        if index_code == "":
            op_string = 'Try again using a valid Index code.'
        else:
            index_quote = nse.get_index_quote(index_code).get('lastPrice')
            op_string = "The last updated price of {} is Rs.{}.".format(index_code.upper(), index_quote)

        return {
            "fulfillmentText": op_string,
            "displayText": '25',
            "source": "webhookdata"
        }

    elif query_result.get('action') == 'get_advances':
        trade_index = query_result.get('parameters').get('index_codes')
        advance_type = query_result.get('parameters').get('advance_type')

        print(trade_index)
        if trade_index == '':
            op_string = 'Try again using a valid Index code.'
        else:
            adv_dec = nse.get_advances_declines()
            
            flag = 0
            for i in adv_dec:
                if i.get('indice') == trade_index:
                    advances = i.get('advances')
                    declines = i.get('declines')
                    flag = 1
                    break
            if flag == 0:
                op_string = "No data of advances/declines for this index was found."
            else:
                if advance_type == 'advance':
                    op_string = "The advances of {} are {}.".format(trade_index, advances)
                else:
                    op_string = "The declines of {} are {}.".format(trade_index, declines)
            print(op_string)

        return {
            "fulfillmentText": op_string,
            "displayText": '25',
            "source": "webhookdata"
        }



if __name__ == '__main__':
    app.run(port=8000,debug=True)