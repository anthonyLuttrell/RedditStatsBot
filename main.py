import datetime
import time
import json
import praw
from filelock import FileLock

total_posts = 0
total_comments = 0
start_seconds = 0
end_seconds = 0

reddit = praw.Reddit(
    client_id="KLDbru6psQuK3GSKc0jfKg",
    client_secret="I7DxzzSMplYt4Bxb_bD5eDEjei8N3Q",
    user_agent="<console:alpha-bot2:1.0>",
    username="Alphabet--bot",
    password="KTL5zm&@Jy75j#a&"
)

subreddit = reddit.subreddit("cooking")
lockfile = "stats.json.lock"
lock = FileLock(lockfile, timeout=1)


def get_stats():

    most_comments = []
    with lock:
        with open("stats.json", "r") as f:
            obj = json.load(f)
            for user in obj["users"]:
                total_user_comments = 0
                total_user_score = 0
                for score in obj["users"][user]["commentScore"]:
                    total_user_comments += 1
                    total_user_score += score
                most_comments.append([str(user), total_user_comments, total_user_score])
    high_scores = most_comments.copy()
    sorted(most_comments, key=lambda x: int(x[1]))
    sorted(high_scores, key=lambda x: int(x[2]))
    # FIXME the sorts are not working right
    print("Most comments: " + most_comments[0][0])
    print("High score: " + high_scores[0][0])


def user_exists(user_id_to_check):
    found = False
    with open("stats.json", "r") as f:
        obj = json.load(f)
        for user in obj["users"]:
            if user_id_to_check == user:
                found = True
                break
    return found


def update_existing(comment_to_update):
    with lock:
        with open("stats.json", "r+") as file_append_existing:
            obj = json.load(file_append_existing)
            users_obj = obj["users"][user_id]

            try:
                index = users_obj["commentId"].index(str(comment_to_update.id))
            except ValueError:
                index = -1

            if index >= 0:
                # if the comment already exists, update the score
                new_score = comment_to_update.score
                users_obj["commentScore"][index] = new_score
            else:
                # if the comment doesn't exist, add the ID and the score
                users_obj["commentId"].append(str(comment_to_update.id))
                users_obj["commentScore"].append(comment_to_update.score)

            file_append_existing.seek(0)
            json.dump(obj, file_append_existing, indent=2)


def add_new(comment_to_add):
    with lock:
        with open("stats.json", "r+") as f:
            new_data = json.load(f)
            new_data["users"][str(comment_to_add.author)] = {"commentId": [comment_to_add.id],
                                                             "commentScore": [comment_to_add.score]}
        with lock:
            with open("stats.json", "w") as f:
                json.dump(new_data, f, indent=2)


while True:
    get_stats()
    start_seconds = time.process_time()

    for submission in subreddit.hot(limit=1000):
        total_posts += 1

        if submission.stickied is False:
            print("Began scanning submission ID: " + str(submission.id) + " at " + time.strftime("%H:%M:%S"))

            for comment in submission.comments:
                total_comments += 1

                if hasattr(comment, "body"):
                    user_id = str(comment.author)

                    if user_id != "None":

                        if user_exists(user_id):
                            update_existing(comment)
                        else:
                            add_new(comment)

    end_seconds = time.process_time()
    log = open("log.txt", "a")
    log.write("\nTime of last loop:      " + str(datetime.timedelta(seconds=end_seconds - start_seconds)))
    log.write("\nTotal posts scanned:    " + str(total_posts))
    log.write("\nTotal comments scanned: " + str(total_comments))
    log.close()
    print("\n********** Main Loop Finished **********\n")
