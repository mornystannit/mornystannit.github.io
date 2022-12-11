import pandas as pd
import matplotlib.pyplot as plt
import requests
from mdutils.mdutils import MdUtils


def get_search_query(title):
    """Parse the question title to get a search query to put into the GDELT API"""
    # NLP stuff goes here
    # but in the meantime...
    return "Russia Ukraine"


def get_gdelt_data(query, timespan="5y"):
    """Get data from the GDELT API for a given query"""
    gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=timelinevol&timespan={timespan}&format=json"
    gdelt_json = requests.get(gdelt_url).json()
    gdelt = pd.DataFrame(gdelt_json['timeline'][0]['data'])
    gdelt['date'] = pd.to_datetime(gdelt['date'])
    gdelt = gdelt.set_index('date')
    return gdelt


def plot_cp_and_news(question, gdelt, search_query, peak_time):
    fig, axs = plt.subplots(nrows=1, ncols=2, sharex=True, figsize=(10, 3))

    xmin = question.index.min()
    xmax = question.index.max()

    question.cp.plot(ax=axs[0], title="Community Prediction", ylim=(0,1))
    axs[0].axvline(x=peak_time, c="orange", lw=5, alpha=0.5)

    gdelt.value.plot(ax=axs[1], title=f"Proportion of worldwide news coverage\nGDELT search for '{search_query}'", xlim=(xmin, xmax))
    axs[1].axvline(x=peak_time, c="orange", lw=5, alpha=0.5)

    fig.tight_layout()



def create_dashboard_assets(questions, changes):
    """Iteratively plot question graphics"""
    mdFile = MdUtils(file_name='index', title='Updates About The World')

    i = 0
    for idx, row in changes.iterrows():
        i += 1
        question = questions[questions['question_id']==idx]

        title = question.title.iloc[0]
        title_short = question.title_short.iloc[0]
        peak_time = pd.Timestamp(row['peak_time'], unit='s')
        search_query = get_search_query(title)
        gdelt = get_gdelt_data(query=search_query)

        plot_cp_and_news(question=question, gdelt=gdelt, search_query=search_query, peak_time=peak_time)

        plot_path = f'assets/{i:02}.png'
        plt.savefig(plot_path)

        mdFile.new_header(level=1, title=title_short)
        mdFile.new_paragraph(mdFile.new_inline_image(text=title_short, path=plot_path))

    mdFile.new_table_of_contents(table_title='Summary', depth=2)
    mdFile.create_md_file()
