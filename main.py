import datetime
import os
import sys
import time
import json
import praw
from praw.exceptions import RedditAPIException
from prawcore import OAuthException

# ******************************************************* BUGS ******************************************************* #
# FIXME when the total_arr length is less than 150 and we sort by total_comments, if there is a tie for total_comments
#       (at least 2 users with the same number of comments), the successive users can have a higher total score than the
#       first user. Example: [["bob", 2, 12, 0],["joe", 2, 23, 0],["john", 2, 45, 0],["jill", 1, 15, 0]]
#       In this case, "bob" would be the Top 1% most helpful, but it should actually be "john"
#
# FIXME the print statements that start with "\r" and end with end="" do not behave the same in the docker logs as they
#       do in the terminal. They should overwrite the existing line in the docker log.
#
# FIXME I do not believe we are handling KeyboardInterrupt correctly when stopping a Docker container

# ************************************************* GLOBAL CONSTANTS ************************************************* #
REDDIT = praw.Reddit("CookingStatsBot", user_agent="r/Cooking Stats Bot by u/96dpi")
SUB = "Cooking"
SUBREDDIT = REDDIT.subreddit(SUB)
NUM_OF_POSTS_TO_SCAN = 1000  # this will include stickied posts, which we are skipping
HOURS = 6
SLEEP_TIME_SECONDS = int(HOURS * 60 * 60)
FLAIR_TEXT = "Top 1% Most Helpful Users of "
MONTHS = ['December', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', '']

# ************************************************* GLOBAL VARIABLES ************************************************* #
start_seconds = 0
end_seconds = 0
previous_day = 31


# ************************************************* GLOBAL CONSTANTS ************************************************* #
def get_stats():
    totals_arr = []
    ratio_arr = []

    # only true on the first iteration on the 1st day of the month
    edit_flair = (int(datetime.datetime.today().day) - previous_day) < 0

    # [ [(string) Username, (int) Total Comments, (int) Total Score, (int) Total Negative Comments] ]
    for user in obj["users"]:
        total_user_comments = 0
        total_user_score = 0
        total_user_negatives = 0
        for score in obj["users"][user]["commentScore"]:
            total_user_comments += 1
            total_user_score += score
            if score < 0:
                total_user_negatives += 1
        totals_arr.append([str(user), int(total_user_comments), int(total_user_score), int(total_user_negatives)])

    if edit_flair:
        # index 1 sorts by comment count
        totals_arr.sort(reverse=True, key=lambda x: x[1])

        # calculate and sort by average comment score (score / count)
        top_1_percent = (round(len(totals_arr) * 0.01))
        for i in range(0, top_1_percent):
            if totals_arr[i][3] == 0:  # skip those with a negative top-level comment
                ratio_arr.append([totals_arr[i][0], round((totals_arr[i][2]) / (totals_arr[i][1]), 2)])

        ratio_arr.sort(reverse=True, key=lambda x: x[1])
        log.write("\n!************* TOP 1% MOST HELPFUL **************!\n")
        log.write("--Top " + str(top_1_percent) + " users out of " + str(len(totals_arr)) + "--\n")

        for i in range(0, len(ratio_arr)):
            log.write("#" + str(i + 1) + " - " + ratio_arr[i - 1][0] + " (" + str(ratio_arr[i - 1][1]) + ")\n")
            flair_string = (FLAIR_TEXT + MONTHS[int(datetime.datetime.today().month) - 1])
            # SUBREDDIT.flair.set(ratio_arr[i][0], text=flair_string)
            print(ratio_arr[i][0] + " -- " + flair_string)


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
        print("\r", "Sleeping since " + sleep_time + ", waking up in " +
              str(SLEEP_TIME_SECONDS - i).rjust(5, "0") + " sec", end="")
        time.sleep(1)


def sys_exit():
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))


# **************************************************** MAIN LOOP ***************************************************** #
try:
    try:
        print("Logged in as:", REDDIT.user.me())
    except OAuthException:
        print("Unable to log in! Verify the credentials in the praw.ini file.")
        sys_exit()

    try:
        SUBREDDIT.mod.accept_invite()
        print("Mod invite accepted from r/" + SUB)
    except RedditAPIException:
        print("No pending mod invites from r/" + SUB + ". Starting main program.")

    total_comments = 0
    last_total_comments = 0

    while True:
        last_total_comments = total_comments
        time_elapsed = 0
        total_posts = 0
        total_comments = 0

        try:
            with open("log/stats.json", "r+") as f:
                obj = json.load(f)
                start_seconds = time.perf_counter()

                for submission in SUBREDDIT.hot(limit=NUM_OF_POSTS_TO_SCAN):

                    if submission.stickied is False:
                        total_posts += 1
                        print("\r", "Began scanning submission ID " +
                              str(submission.id) + " at " + time.strftime("%H:%M:%S"), end="")

                        for comment in submission.comments:
                            if hasattr(comment, "body") and not comment.distinguished:
                                user_id = str(comment.author)
                                total_comments += 1

                                if user_id != "None":
                                    if user_exists(user_id):
                                        update_existing(comment)
                                    else:
                                        add_new(comment)

                            time.sleep(0.1)  # avoids HTTP 429 errors
                    time.sleep(0.1)  # avoids HTTP 429 errors

            end_seconds = time.perf_counter()
            time_elapsed += (end_seconds - start_seconds) / 60
            print("\nTime elapsed: " + str(datetime.timedelta(minutes=time_elapsed)))
            log = open("log/log.txt", "w")  # intentionally overwriting the entire file content
            log.write("!************** Main Loop Finished **************!")
            log.write("\nTime of last loop:      " + str(datetime.timedelta(seconds=(end_seconds - start_seconds))))
            log.write("\nTotal posts scanned:    " + str(total_posts))
            log.write("\nTotal comments scanned: " + str(total_comments))
            log.write("\nNew comments scanned:   " + str(total_comments - last_total_comments))
            get_stats()
            log.close()
            try:
                with open("log/stats.json", "w") as f:
                    f.seek(0)
                    json.dump(obj, f, indent=2)
                sleep()
                previous_day = datetime.datetime.today().day
            except FileNotFoundError:
                print("File Not Found, exiting.")
                sys_exit()
        except FileNotFoundError:
            print("File Not Found, exiting.")
            sys_exit()

except KeyboardInterrupt:
    # catches Ctrl+C and IDE program interruption to ensure we write to the json file
    try:
        print("\n-- Process halted, dumping JSON file --")
        with open("log/stats.json", "w") as f:
            f.seek(0)
            json.dump(obj, f, indent=2)
    except NameError:
        sys_exit()
    sys_exit()
