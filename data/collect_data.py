from tqdm import tqdm 
import praw
from psaw import PushshiftAPI
import datetime as dt
import pandas as pd
from dateutil.relativedelta import relativedelta



timestamp = int(dt.datetime(2022,5,18,0,0).timestamp())

api = PushshiftAPI()
### add more variance for search terms if you think its good
q = "monkeypox | monkey pox"
### set limit to be number of posts we want to collect
### i think maybe 5k might be a good enough size to get a good enough comment base 
submissions = api.search_submissions(q=q, limit=2000)

c = 0

posts = []

for post in submissions:
    c += 1
    try:
        body = post.body
    except Exception as e:
        body = ''
    subreddit = post.subreddit
    
    posts.append([post.title, body, post.subreddit, post.id, post.created_utc, post.author])

posts = pd.DataFrame(posts, columns=["Title", "Body", "Subreddit", "Id", "Created UTC", "Author"])
posts
posts.to_csv("posts.csv", index=False)


reddit = praw.Reddit(
    client_id="piXz-eLpTpGmahnm2EPScw",
    client_secret="hUE09YbC09uQUiahDDXC_ihd1cZG5w",
    user_agent="MonkeyPoxDiscussionScraper"
)

leftmost_comments_per_post = []
for submission_id in tqdm(posts['Id']):
  post_comments = [submission_id, [], []]
  submission = reddit.submission(submission_id)
  try: 
    ### try setting limit to 0; it effectively removes pagination and should speed up the script
    submission.comments.replace_more(limit=None)
    comment_queue = [submission.comments[0]]  # Seed with top-level first comment thread; change to [:] for all branches
                                              # not just left-most
    if comment_queue[0].author.name == "AutoModerator":
          ### honestly not sure if this will work to replace the automoderator comments with the next left-most top level comment thread
          try:
            comment_queue = [submission.comments[1]]
          except:
            continue ## will continue move us to the next instance in the for loop? i don't know how to program
    while comment_queue:
      comment = comment_queue.pop(0)
      post_comments[1].append(comment.body)
      post_comments[2].append(comment.author.name)
      comment_queue.extend(comment.replies)
    leftmost_comments_per_post.append(post_comments)
  except:
    leftmost_comments_per_post.append(post_comments)
  
leftmost_comments_per_post = pd.DataFrame(leftmost_comments_per_post, columns=["Id", "Comments"]) ### might want to collect comment authors
leftmost_comments_per_post.to_csv("leftmost.csv", index=False)

leftmost_comments_per_post.head()

