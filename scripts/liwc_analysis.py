import liwc
import pandas as pd
import numpy as np
import re
from collections import Counter
from tqdm import tqdm
from ast import literal_eval
import itertools
from typing import Union


# file for original un-LIWC'd labeled data
DF_FILEPATH = 'notebooks/final_cleaned_data.xlsx'
LIWC_FILEPATH = 'data/LIWC2015_English.dic'
LIWC_SCORES_FILEPATH = 'data/liwc_scores.xlsx'

#### HELPER METHODS FOR TOKENIZING AND LIWC PARSING A DISCUSSION#################################################

# tokenizes a sentence turning it into an ITERATOR (NOT A LIST)


def tokenize(input_sentence: str):
    # you may want to use a smarter tokenizer
    for match in re.finditer(r'\w+', input_sentence, re.UNICODE):
        yield match.group(0)  # this is a generator not a list

# wrapper for the tokenize method that converts iterator to list


def get_sentence_parse(input_sentence: str):
    return list(tokenize(input_sentence))


# gets the liwc category counts for a string using the liwc parse function
def get_liwc_cats_for_comment(comment: str, parse_function):
    if type(comment) != str:
        return []
    comment_tokens = get_sentence_parse(comment)
    counter = Counter(
        category for token in comment_tokens for category in parse_function(token))
    return counter.most_common()

###################################################################################################

# Takes a df of samples and then creates a new dataframe with the liwc counts per row per comment
# as well asf or the whole discussion


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
            get_liwc_cats_for_comment(str(row["C1"]) + str(row["C2"]) + str(row["C3"]), parse))

    df["C1_LIWC"] = pd.Series(comment_liwc_categories[0])
    df["C2_LIWC"] = pd.Series(comment_liwc_categories[1])
    df["C3_LIWC"] = pd.Series(comment_liwc_categories[2])
    df["Whole_Discussion_LIWC"] = pd.Series(comment_liwc_categories[3])

    df.to_excel(scores_filepath, index=False)
    return df


def get_categories_avg_per_discussion_for_row(row: pd.Series):
    whole_discussion_tok = get_sentence_parse(
        row["C1"] + row["C2"] + row["C3"])
    len_whole_discussion = len(whole_discussion_tok)
    # the list was saved as a string so we literal_eval to reconvert back to list
    category_counts = literal_eval(row["Whole_Discussion_LIWC"])
    category_avgs = []
    for (category, count_in_disc) in category_counts:
        category_avgs.append((category, count_in_disc / len_whole_discussion))

    return category_avgs


def get_categories_avg_per_discussion_for_category(liwc_category: str, col_name: str, col_val: Union[str, int], df: pd.DataFrame):
    # for all rows that have some value (e.g. all rows with Serious == 1)
    subselection = df.loc[df[col_name] == col_val]
    # get the number of samples with this value
    num_samples_in_subselection = subselection.shape[0]

    # for all samples with this qualification, we want to see if that sample has the particular liwc category of interest present
    for i, row in tqdm(subselection.iterrows()):
        whole_discussion_liwc_scores = literal_eval(
            row["Whole_Discussion_LIWC"])
        avgs = get_categories_avg_per_discussion_for_row(row)
        category_avg = 0
        # average the liwc score per word across all samples
        for category, row_avg_value in avgs:
            if category == liwc_category:
                category_avg += row_avg_value

    return category_avg / num_samples_in_subselection
