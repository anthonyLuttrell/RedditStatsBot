import datetime
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

SUB = "cooking"
NUM_OF_POSTS_TO_SCAN = 1000  # this will include stickied posts
MINUTES_TO_RUN = 120
time_elapsed = 0.0
total_posts = 0
total_comments = 0
start_seconds = 0
end_seconds = 0

SUBREDDIT = reddit.subreddit(SUB)


def get_stats():
    totals_arr = []
    ratio_arr = []

    # build an array in the format [ [(string) Username, (int) Total Comments, (int) Total Score] ]
    for user in obj["users"]:
        total_user_comments = 0
        total_user_score = 0
        for score in obj["users"][user]["commentScore"]:
            total_user_comments += 1
            total_user_score += score
        totals_arr.append([str(user), int(total_user_comments), int(total_user_score)])

    # sort by total score
    totals_arr.sort(reverse=True, key=lambda x: x[2])
    log.write("\n!***************** HIGH SCORE *******************!\n")
    for i in range(1, 101):
        log.write("#" + str(i) + " - " + totals_arr[i - 1][0] + " (" + str(totals_arr[i - 1][2]) + ")\n")

    # sort by comment count
    totals_arr.sort(reverse=True, key=lambda x: x[1])
    log.write("\n!********** MOST PROLIFIC COMMENTERS ************!\n")
    for i in range(1, 101):
        log.write("#" + str(i) + " - " + totals_arr[i - 1][0] + " (" + str(totals_arr[i - 1][1]) + ")\n")

    # calculate and sort by ratio (score / count)
    log.write("\n!************* TOP 1% MOST HELPFUL **************!\n")
    top_1_percent = (len(totals_arr) * 0.01)
    for i in range(0, round(top_1_percent)):
        # totals_arr is currently sorted by  most comments first
        ratio_arr.append([totals_arr[i][0], round((totals_arr[i][2]) / (totals_arr[i][1]), 2)])
    ratio_arr.sort(reverse=True, key=lambda x: x[1])
    for i in range(1, round(top_1_percent)):
        log.write("#" + str(i) + " - " + ratio_arr[i - 1][0] + " (" + str(totals_arr[i - 1][1]) + ")\n")


def user_exists(user_id_to_check):
    found = False
    for user in obj["users"]:
        if user_id_to_check == user:
            found = True
            break
    return found


def update_existing(comment_to_update):
    users_obj = obj["users"][user_id]
    id_arr = users_obj["commentId"]
    score_arr = users_obj["commentScore"]

    try:
        index = id_arr.index(str(comment_to_update.id))
    except ValueError:
        index = -1

    if index >= 0:
        # comment already exists, update the score
        score_arr[index] = comment_to_update.score
    else:
        # comment does not exist, add new comment and score
        id_arr.append(str(comment_to_update.id))
        score_arr.append(comment_to_update.score)


def add_new(comment_to_add):
    obj["users"][str(comment_to_add.author)] = {"commentId": [comment_to_add.id],
                                                "commentScore": [comment_to_add.score]}


print("Logged in as: ", reddit.user.me())

while time_elapsed <= MINUTES_TO_RUN:
    total_posts = 0
    total_comments = 0

    with open("stats.json", "r+") as f:
        obj = json.load(f)
        start_seconds = time.perf_counter()

        for submission in SUBREDDIT.hot(limit=NUM_OF_POSTS_TO_SCAN):

            if submission.stickied is False:
                total_posts += 1
                print("\r", "Began scanning submission ID " +
                      str(submission.id) + " at " + time.strftime("%H:%M:%S"), end="")

                for comment in submission.comments:
                    total_comments += 1

                    if hasattr(comment, "body"):
                        user_id = str(comment.author)

                        if user_id != "None":

                            if user_exists(user_id):
                                update_existing(comment)
                            else:
                                add_new(comment)

    end_seconds = time.perf_counter()
    time_elapsed += (end_seconds - start_seconds) / 60
    print("\nMinutes elapsed: " + str(round(time_elapsed, 2)))
    print("\n!************** Main Loop Finished **************!\n")
    log = open("log.txt", "a")
    log.write("\n!************** Main Loop Finished **************!")
    log.write("\nTime of last loop:      " + str(datetime.timedelta(seconds=(end_seconds - start_seconds))))
    log.write("\nTotal posts scanned:    " + str(total_posts))
    log.write("\nTotal comments scanned: " + str(total_comments))
    get_stats()
    log.close()
    with open("stats.json", "w") as f:
        f.seek(0)
        json.dump(obj, f, indent=2)
