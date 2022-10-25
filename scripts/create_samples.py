import praw
import re
import pandas as pd
from praw.models.comment_forest import CommentForest
from typing import List
from dataclasses import dataclass
import time

reddit = praw.Reddit(
    client_id="piXz-eLpTpGmahnm2EPScw",
    client_secret="hUE09YbC09uQUiahDDXC_ihd1cZG5w",
    user_agent="MonkeyPoxDiscussionScraper"
)

@dataclass
class Comment:
  comment_id: str
  author: str
  text: str

class CommentRetriever:
  def get_comment_chains(self, submission_id: int) -> List[List[Comment]]:
    submission = reddit.submission(submission_id)
    submission.comments.replace_more()
    comment_chains = []
    self.dfs([], submission.comments, comment_chains)
    return comment_chains

  def dfs(self, cur_chain: List[Comment], comments: CommentForest, comment_chains: List[List[Comment]]) -> None:
    if len(comments) == 0:
      comment_chains.append(cur_chain)
      return
    for comment in comments:
      new_chain = cur_chain + [Comment(comment.id, comment.author if comment.author else '[deleted]', re.sub('\n', '', comment.body))]
      self.dfs(new_chain, comment.replies, comment_chains)

def format_chain(comment_chain: List[Comment]) -> str:
  return '\n'.join(f'{comment.author}: {comment.text}' for comment in comment_chain)


posts = pd.read_csv('data/large_posts.csv')

cr = CommentRetriever()
comment_sets = []
curr_ind = 0

for ind in range(curr_ind, len(posts.index)): 
    print('INDEX: ', ind)
    print('TITLE: ',posts.loc[ind, 'Title'])
    if not re.search('(monkeypox|monkey pox)', posts.loc[ind, 'Title'].lower()):
      continue

    try:
      comment_chains = cr.get_comment_chains(posts.loc[ind, 'Id'])
    except:
      time.sleep(2)
      curr_ind = ind
      print('pause')
      try:
        comment_chains = cr.get_comment_chains(posts.loc[ind, 'Id'])
      except:
        ind += 1

    print('post id = ',id)
    print('len_chains = ',len(comment_chains))
    
    for comment_chain in comment_chains:
        print('chain_length = ',len(comment_chain))
        if len(comment_chain) >= 3:
            print(format_chain(comment_chain))
            for i in range(2,len(comment_chain)):
                nums = list(range(i-2,i+1))
                add = {'ID': posts.loc[ind, 'Id'], **{'C'+ str(c+1) :comment_chain[nums[c]].text for c in range(3)}, **{'A'+ str(c+1) :comment_chain[nums[c]].author for c in range(3)}}
                print(add)
                comment_sets.append(add)
    print('Comment Set Size = ', len(comment_sets))
    if ind%25 == 0:
      df = pd.DataFrame(comment_sets)
      df = df.dropna().reset_index()
      df.to_excel(f'data/samples/samples_checkpoint_{ind}.xlsx')

df = pd.DataFrame(comment_sets)
df = df.dropna().reset_index()
df.to_excel('data/samples/samples.xlsx')