# Get data for recent questions from the Metaculus API

import requests
import pandas as pd
from tqdm import tqdm
import datetime
import time

def scrape_metaculus(url, n=None):
    """
    url is the URL you want to scrape
    n is the number of pages you want, if n is None (default) then runs forever
    """

    # This is so you can get a counter for the infinite while loop using tqdm
    def generator():
        while url is not None and i is not n:
            yield

    i = 0
    json_list = []

    # Use a session to make requests slightly quicker
    s = requests.Session()

    for _ in tqdm(generator()):
        try:
            response = s.get(url)
            json_raw = response.json()
            json_list.extend(json_raw['results'])
            url = json_raw['next']
            i += 1
        except KeyError:
            # if 'results' not in response then likely rate limited
            # if so then wait for the specified period in the 'Retry-After' header and then try again
            if response.status_code == 429:
                retry_after = int(response.headers['Retry-After'])
                print(f"Response status {response.status_code}, waiting for {retry_after} seconds.")
                time.sleep(retry_after + 1)
                continue
    
    return(json_list)


def clean_recent_questions(df, days=30):
    """Clean the questions dataset and return recent questions.
    
    df: the dataframe to clean, from the Metaculus API
    days: the number of days to look for recent activity in
    """

    cutoff_date = pd.to_datetime(datetime.datetime.now().date()) - pd.to_timedelta(days, unit='day') 

    recent = df[
        [
            'id',
            'page_url',
            'title',
            'title_short',
            'last_activity_time',
            'possibilities.type',
            'prediction_timeseries',
            'number_of_predictions'
        ]
    ]

    recent['page_url'] = recent['page_url'].apply(lambda x: 'https://www.metaculus.com' + x)
    recent['last_activity_time'] = pd.to_datetime(df['last_activity_time']).dt.date
    recent = recent[
        (recent['last_activity_time'] > pd.to_datetime(cutoff_date))
        & (recent['possibilities.type']=='binary')
        & (recent['number_of_predictions']>1)
    ]

    # Explode prediction timeseries so each row is one prediction at time t
    recent = recent.explode('prediction_timeseries')
    recent = pd.concat([recent, recent['prediction_timeseries'].apply(pd.Series)], axis=1)
    recent = pd.concat([recent, recent['distribution'].apply(pd.Series)], axis=1)

    # Set index to time of prediction, as in provided data
    recent['time'] = pd.to_datetime(recent['t'], unit='s')
    recent = recent.set_index('time')

    recent = recent.rename(
    columns = {
        'id' : 'question_id',
        'community_prediction' : 'cp',
        'num_predictions' : 'n_predictions_at_t',
        'number_of_predictions' : 'n_predictions_total',
        'num' : 'distribution_num',
        'avg' : 'distribution_avg',
        'var' : 'distribution_var',
    }
    )

    # drop columns
    recent = recent[[x for x in recent.columns if type(x) is not int]]
    recent = recent.drop(['prediction_timeseries', 'distribution'], axis=1)
    return recent


def get_recent_questions(days=30, n=None):
    """Wrapper function to contain everything"""
    questions = scrape_metaculus(url="https://www.metaculus.com/api2/questions/?limit=100&offset=0", n=n)
    questions = pd.json_normalize(questions)
    questions = clean_recent_questions(questions, days)
    return questions
