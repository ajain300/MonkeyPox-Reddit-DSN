import liwc
import pandas as pd
import numpy as np
import re
from collections import Counter
from tqdm import tqdm
from ast import literal_eval
import itertools
from typing import Union
from scipy import stats


# file for original un-LIWC'd labeled data
DF_FILEPATH = 'data/total_comment_labels.xlsx'
LIWC_FILEPATH = 'data/LIWC2015_English.dic'
LIWC_SCORES_FILEPATH = 'data/labels_liwc_scores.xlsx'

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


### returns a list of tuples of form (liwc category, #counts of category / discussion length)
### e.g. [("informal (Informal Language)", .32), ("persconc (Personal Concerns)", 0.21), .....]
def get_categories_avg_per_discussion_for_row(row: pd.Series):
    whole_discussion_tok = get_sentence_parse(
        row["C1"] + row["C2"] + row["C3"])
    len_whole_discussion = len(whole_discussion_tok)
    # the list was saved as a string so we literal_eval to reconvert back to list
    category_counts = literal_eval(row["Whole_Discussion_LIWC"])
    category_avgs = []
    for (category, count_in_discussion) in category_counts:
        category_avgs.append((category, count_in_discussion / len_whole_discussion))

    return category_avgs


### applies the above method for all samples for a whole subsection of a column
### subsection is chosen based on the column name and value (e.g. df["ag"] == 1)
### takes the average liwc score for a specific liwc category and takes a final average overall samples
### in that subsection of the dataframe
def get_liwc_category_avg_for_single_col_subsample(liwc_category: str, col_name: str, col_val: Union[str, int], df: pd.DataFrame):
    # for all rows that have some value (e.g. all rows with Serious == 1)
    subselection = df.loc[df[col_name] == col_val]
    # get the number of samples with this value
    num_samples_in_subselection = subselection.shape[0]

    # for all samples with this qualification, we want to see if that sample has the particular liwc category of interest present
    category_avg = 0
    category_row_scores = []
    for _, row in tqdm(subselection.iterrows()):  # for each sample in this subselection
        avgs = get_categories_avg_per_discussion_for_row(row)
        row_score = 0
        # average the liwc score per word across all samples
        for category, row_avg_value in avgs:
            if category == liwc_category:
                category_avg += row_avg_value
                row_score += row_avg_value
        category_row_scores.append(row_score)

    return category_avg / num_samples_in_subselection, category_row_scores

def get_p_vals_for_two_subsamples(category: str, col_name_1: str, col_val_1: Union[str, int],
                                   col_name_2: str, col_val_2: Union[str, int], 
                                  df: pd.DataFrame):
    subsample_1_scores = get_liwc_category_avg_for_single_col_subsample(
        category, col_name=col_name_1, col_val=col_val_1, df=df)
    subsample_2_scores = get_liwc_category_avg_for_single_col_subsample(
        category, col_name=col_name_2, col_val=col_val_2, df=df)

    
    ttest = stats.ttest_ind(subsample_1_scores[1], subsample_2_scores[1], equal_var=False)
    print("subsample 1 mean is " + str(np.mean(subsample_1_scores[1])))
    print("subsample 1 std dv is: " + str(np.std(subsample_1_scores[1])))
    print("subsample 2 mean is " + str(np.mean(subsample_2_scores[1])))
    print("subsample 2 std dv is: " + str(np.std(subsample_2_scores[1])))
    return ttest

### applies the get_categories_avg_per_discussion_for_row method for all samples for a whole subsection of a column
### subsection is chosen based on three column values for the 'ag', 'ci', and 'se' columns
### takes the average liwc score for a specific liwc category and takes a final average overall samples
### in that subsection of the dataframe
def get_liwc_category_avg_for_multiple_cols_subsample(liwc_category: str, col_val_1: int, col_val_2: int, col_val_3: int, df: pd.DataFrame):
    # for all rows that have some value (e.g. all rows with Serious == 1)
    subselection = df.loc[(df['ag'] == col_val_1) & (df['ci'] == col_val_2) & (df['se'] == col_val_3)]
    # get the number of samples with this value
    num_samples_in_subselection = subselection.shape[0]

    # for all samples with this qualification, we want to see if that sample has the particular liwc category of interest present
    category_avg = 0
    category_row_scores = []
    for _, row in tqdm(subselection.iterrows()):  # for each sample in this subselection
        avgs = get_categories_avg_per_discussion_for_row(row)
        row_score = 0
        # average the liwc score per word across all samples
        for category, row_avg_value in avgs:
            if category == liwc_category:
                category_avg += row_avg_value
                row_score += row_avg_value
        category_row_scores.append(row_score)

    return category_avg / num_samples_in_subselection, category_row_scores

def get_p_vals_for_two_subsamples_mult_cols(category: str, col_val_1: Union[str, int],
                                    col_val_2: Union[str, int], col_val_3: Union[str, int], 
                                    col_val_4: Union[str, int], col_val_5: Union[str, int],
                                    col_val_6: Union[str, int],
                                  df: pd.DataFrame):
    subsample_1_scores = get_liwc_category_avg_for_multiple_cols_subsample(
        category, col_val_1==col_val_1, col_val_2=col_val_2, col_val_3=col_val_3, df=df)
    subsample_2_scores = get_liwc_category_avg_for_multiple_cols_subsample(
        category, col_val_1==col_val_4, col_val_2=col_val_5, col_val_3=col_val_6, df=df)

    
    ttest = stats.ttest_ind(subsample_1_scores[1], subsample_2_scores[1], equal_var=False)
    print("subsample 1 mean is " + str(np.mean(subsample_1_scores[1])))
    print("subsample 1 std dv is: " + str(np.std(subsample_1_scores[1])))
    print("subsample 2 mean is " + str(np.mean(subsample_2_scores[1])))
    print("subsample 2 std dv is: " + str(np.std(subsample_2_scores[1])))
    return ttest


df = pd.read_excel(LIWC_SCORES_FILEPATH)
liwc_category = 'informal (Informal Language)'
# col_name_1 = 'ci'
# col_val_1 = 1
# col_name_2 = 'ci'
# col_val_2 = 0
# pvals = get_p_vals_for_two_subsamples(liwc_category, col_name_1=col_name_1, col_val_1=col_val_1, col_name_2=col_name_2, col_val_2=col_val_2, df=df)
# print(pvals)


pvals = get_p_vals_for_two_subsamples_mult_cols(liwc_category, 0,0,0, 0,0,1, df=df)
print(pvals)