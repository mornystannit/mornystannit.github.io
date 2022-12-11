# Run the pipeline to update the dashboard

import importlib
pipeline_01 = importlib.import_module("01_get_recent_questions")
#pipeline_02 = importlib.import_module("02_find_significant_changes") # DOES NOT EXIST YET
#pipeline_03 = importlib.import_module("03_create_dashboard_assets") # DOES NOT EXIST YET


questions = pipeline_01.get_recent_questions(days=30)
""" Get binary questions that have been recently active in the last `days` days
Parameters:
    days: the cutoff for 'recent' questions is set as this many days ago

Returns:
    questions: DataFrame of community prediction over time on recent questions
        Columns:
            time                    (index)
            question_id
            page_url
            title
            title_short
            last_activity_time
            possibilities.type      (binary)
            n_predictions_total
            t
            cp
            n_predictions_at_t
            distribution_num
            distribution_avg
            distribution_var
"""


changes = pipeline_02.find_significant_changes(questions=questions)
""" Get significant changes for questions
Parameters:
    questions: DataFrame of community prediction over time on recent questions.
        Each row represents the community prediction at a time t.

Returns:
    changes: DataFrame of community predictions on recent questions.
        Each row represnts one question.
        Columns:
            question_id
            peak_time:      time of the peak
            (something about peak relative size?)
"""


pipeline_03.create_dashboard_assets(questions=questions, changes=changes)
""" Create assets for dashboard
    - overwrite index.MD with new question titles
    - create plot of community prediction and news interest over time    

Parameters:
    questions: DataFrame of community prediction over time on recent questions.
        Each row represents the community prediction at a time t.

    changes: DataFrame of community predictions on recent questions.
        Each row represnts one question.

Returns:
    None
"""