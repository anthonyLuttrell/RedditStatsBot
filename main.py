import time
import json
import praw

reddit = praw.Reddit(
    client_id="KLDbru6psQuK3GSKc0jfKg",
    client_secret="I7DxzzSMplYt4Bxb_bD5eDEjei8N3Q",
    user_agent="<console:alpha-bot2:1.0>",
    username="Alphabet--bot",
    password="KTL5zm&@Jy75j#a&"
)

subreddit = reddit.subreddit("cooking")


def user_exists(user_id):
    found = False
    file = open("stats.json", "r")
    data = json.load(file)
    for user in data["users"]:
        if user_id == user["userId"]:
            found = True
            break
    file.close()
    return found


while True:
    for submission in subreddit.hot(limit=1000):
        if submission.stickied is False:
            for comment in submission.comments:
                if hasattr(comment, "body"):
                    if comment.author is not None:
                        # fileWrite = open("stats.json", "a")
                        # userData = json.load(fileWrite)
                        if user_exists(comment.author):
                            print("User exists: " + comment.author)
                            # userData[comment.author]["commentArr"] += comment.body
                            time.sleep(3)
                        else:
                            print("Adding new user: " + str(comment.author))
                            with open("stats.json", "r+") as fileAppend:
                                newData = json.load(fileAppend)
                                newData["users"].append({"userId": str(comment.author),
                                                         "voteCount": comment.score,
                                                         "commentArr": [str(comment.id)]})
                                fileAppend.seek(0)
                                json.dump(newData, fileAppend, indent=2)
                            # userData += {str(comment.author): [{}]}
                            # newUser = {}
                            # userData["users"] += newUser

# TODO implement method for "downvote to remove"
