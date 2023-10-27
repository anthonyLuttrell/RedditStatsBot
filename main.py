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
    obj = json.load(file)
    for user in obj["users"]:
        if user_id == user:
            found = True
            break
    return found


while True:
    for submission in subreddit.hot(limit=1000):
        if submission.stickied is False:
            for comment in submission.comments:
                if hasattr(comment, "body"):
                    user = str(comment.author)
                    if user is not None:
                        # fileWrite = open("stats.json", "a")
                        # userData = json.load(fileWrite)
                        if user_exists(user):
                            print("User exists: " + user)
                            with open("stats.json", "r+") as fileExAppend:
                                userObj = json.load(fileExAppend)
                                tempUserObj = userObj["users"][user]
                                try:
                                    index = tempUserObj["commentId"].index(str(comment.id))
                                except ValueError:
                                    index = -1
                                if index >= 0:
                                    # if the comment already exists, update the score
                                    newScore = comment.score
                                    tempUserObj["commentScore"][index] = newScore
                                else:
                                    # if the comment doesn't exist, add the ID and the score
                                    tempUserObj["commentId"].append(str(comment.id))
                                    tempUserObj["commentScore"].append(comment.score)
                                fileExAppend.seek(0)
                                json.dump(userObj, fileExAppend, indent=2)
                        else:
                            print("Adding new user: " + str(user))
                            with open("stats.json", "r+") as fileAppend:
                                newData = json.load(fileAppend)
                                newData["users"][str(comment.author)] = {"commentId": [comment.id],
                                                                         "commentScore": [comment.score]}
                                fileAppend.seek(0)
                                json.dump(newData, fileAppend, indent=2)