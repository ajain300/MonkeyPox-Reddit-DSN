import liwc
import pandas as pd
import numpy as np
import re
from collections import Counter
from tqdm import tqdm
from ast import literal_eval


DF_FILEPATH = 'data/samples/initial_labeled_data.xlsx'
LIWC_FILEPATH = 'data/LIWC2015_English.dic'
LIWC_SCORES_FILEPATH = 'data/liwc_scores.xlsx'

#### HELPER METHODS FOR TOKENIZING AND LIWC PARSING A DISCUSSION#################################################


def tokenize(input_sentence: str):
    # you may want to use a smarter tokenizer
    for match in re.finditer(r'\w+', input_sentence, re.UNICODE):
        yield match.group(0) ### this is a generator not a list


def get_sentence_parse(input_sentence: str):
    return tokenize(input_sentence)


def get_liwc_cats_for_comment(comment: str, parse_function):
    comment_tokens = get_sentence_parse(comment)
    counter = Counter(
        category for token in comment_tokens for category in parse_function(token))
    return counter.most_common()

###################################################################################################


def build_liwc_excel_for_samples(df_filepath: str, liwc_filepath: str, scores_filepath: str):
    df = pd.read_excel(df_filepath, index_col=0)
    comment_liwc_categories = [[], [], [], []]
    parse, category_names = liwc.load_token_parser(liwc_filepath)
    for i, row in tqdm(df.iterrows()):
        comment_liwc_categories[0].append(
            get_liwc_cats_for_comment(row["C1"], parse))
        comment_liwc_categories[1].append(
            get_liwc_cats_for_comment(row["C2"], parse))
        comment_liwc_categories[2].append(
            get_liwc_cats_for_comment(row["C3"], parse))
        comment_liwc_categories[3].append(
            get_liwc_cats_for_comment(row["C1"] + row["C2"] + row["C3"], parse))

    df["C1_LIWC"] = pd.Series(comment_liwc_categories[0])
    df["C2_LIWC"] = pd.Series(comment_liwc_categories[1])
    df["C3_LIWC"] = pd.Series(comment_liwc_categories[2])
    df["Whole_Discussion_LIWC"] = pd.Series(comment_liwc_categories[3])

    df.to_excel(scores_filepath, index=False)
    return df


def get_categories_avg_per_discussion_for_row(row: pd.Series):
    whole_discussion_tok = get_sentence_parse(row["C1"] + row["C2"] + row["C3"])
    len_whole_discussion = len(list(whole_discussion_tok))
    ### the list was saved as a string so we literal_eval to reconvert back to list
    category_counts = literal_eval(row["Whole_Discussion_LIWC"])
    category_avgs = []
    for (category, count_in_disc) in category_counts:
        category_avgs.append((category, count_in_disc / len_whole_discussion))

    return category_avgs


def get_categories_avg_per_discussion_for_category(category: str, df: pd.DataFrame):
    
