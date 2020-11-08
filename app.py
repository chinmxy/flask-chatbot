from flask import Flask, request, make_response, jsonify
import time
import datetime
# from fuzzysearch import find_near_matches

from nsetools import Nse
from pprint import pprint

# importing the module 
import json 

app = Flask(__name__)

@app.route('/')
def index():
    return 'Server is running is at port 8000' 

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    nse = Nse()
    # Opening JSON file 
    with open('symbols.json') as json_file: 
        symbol_data = json.load(json_file) 
  
    req = request.get_json(silent=True, force=True)
    print(req)

    query_result = req.get('queryResult').get('parameters')
    price_type = query_result.get('price_type')
    company_name = query_result.get('company_name')
    date_time = query_result.get('date-time')


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
        # with open('symbols.json', 'rb') as f:
        #     print(find_near_matches_in_file(company_name, f, max_l_dist=1))

    except:
        return {
            "fulfillmentText": "Sorry! This company does not belong to NSE.",
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


if __name__ == '__main__':
    app.run(port=8000,debug=True)