import pandas as pd
import matplotlib.pyplot as plt

def create_dashboard_assets(questions, changes):
    i = 1
    for idx, rows in changes.iterrows():
        question = questions[questions['question_id']==idx]
        question.cp.plot()
        plt.savefig(f'assets/{i:02}.png')
