import datetime
import os
import sys
import time
import json
import praw

# TODO update user flair on the 1st of every month using UTC time
reddit = praw.Reddit("CookingStatsBot", user_agent="Karma Stats Bot by u/96dpi")

SUB = "Cooking"
NUM_OF_POSTS_TO_SCAN = 1000  # this will include stickied posts
HOURS = 6
SLEEP_TIME_SECONDS = int(HOURS * 60 * 60)
start_seconds = 0
end_seconds = 0
flair_saved = False
previous_day = 0

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

    length = 101 if len(totals_arr) >= 100 else (len(totals_arr) + 1)
    # index 2 sorts by total score
    totals_arr.sort(reverse=True, key=lambda x: x[2])
    log.write("\n!***************** HIGH SCORE *******************!\n")
    log.write("--Top " + str(length - 1) + " users out of " + str(len(totals_arr)) + "--\n")
    for i in range(1, length):
        log.write("#" + str(i) + " - " + totals_arr[i - 1][0] + " (" + str(totals_arr[i - 1][2]) + ")\n")

    # index 1 sorts by comment count
    totals_arr.sort(reverse=True, key=lambda x: x[1])
    log.write("\n!********** MOST PROLIFIC COMMENTERS ************!\n")
    log.write("--Top " + str(length - 1) + " users out of " + str(len(totals_arr)) + "--\n")
    for i in range(1, length):
        log.write("#" + str(i) + " - " + totals_arr[i - 1][0] + " (" + str(totals_arr[i - 1][1]) + ")\n")

    # calculate and sort by ratio (score / count)
    log.write("\n!************* TOP 1% MOST HELPFUL **************!\n")
    top_1_percent = (round(len(totals_arr) * 0.01))
    log.write("--Top " + str(top_1_percent - 1) + " users out of " + str(len(totals_arr)) + "--\n")
    for i in range(0, round(top_1_percent)):
        # totals_arr is currently sorted by most comments first
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


def sleep():
    sleep_time = time.strftime("%H:%M:%S")
    for i in range(0, SLEEP_TIME_SECONDS):
        time.sleep(1)
        print("\r", "Sleeping since " + sleep_time +
              ", waking up in " + str(SLEEP_TIME_SECONDS - i).rjust(5, "0") + " sec", end="")


def edit_flair():
    print("No flair to edit :-(")


try:
    print("Logged in as: ", reddit.user.me())
    total_comments = 0
    last_total_comments = 0
    while True:
        if int(datetime.datetime.today().day) - previous_day < 0:
            # only true on the first iteration on the 1st day of the month
            edit_flair()
        last_total_comments = total_comments
        time_elapsed = 0
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
                        if hasattr(comment, "body") and not comment.stickied:
                            total_comments += 1
                            user_id = str(comment.author)

                            if user_id != "None":
                                if user_exists(user_id):
                                    update_existing(comment)
                                else:
                                    add_new(comment)
                        time.sleep(0.1)  # avoids HTTP 429 errors
                time.sleep(0.1)  # avoids HTTP 429 errors

        end_seconds = time.perf_counter()
        time_elapsed += (end_seconds - start_seconds) / 60
        print("\nMinutes elapsed: " + str(round(time_elapsed, 2)))
        log = open("log.txt", "w")  # intentionally overwriting the entire file content
        log.write("\n!************** Main Loop Finished **************!")
        log.write("\nTime of last loop:      " + str(datetime.timedelta(seconds=(end_seconds - start_seconds))))
        log.write("\nTotal posts scanned:    " + str(total_posts))
        log.write("\nTotal comments scanned: " + str(total_comments))
        log.write("\nNew comments scanned:   " + str(total_comments - last_total_comments))
        get_stats()
        log.close()
        with open("stats.json", "w") as f:
            f.seek(0)
            json.dump(obj, f, indent=2)
        sleep()
        previous_day = datetime.datetime.today().day

except KeyboardInterrupt:
    # catches Ctrl+C and IDE program interruption to ensure we write to the json file
    try:
        with open("stats.json", "w") as f:
            f.seek(0)
            json.dump(obj, f, indent=2)
    except NameError:
        try:
            sys.exit(130)
        except SystemExit:
            os.system(exit(130))
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))
