import datetime
import math
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
BOT_NAME = "CookingStatsBot"
REDDIT = praw.Reddit(BOT_NAME, user_agent="r/Cooking Stats Bot by u/96dpi")
SUB = "Cooking"
SUBREDDIT = REDDIT.subreddit(SUB)
NUM_OF_POSTS_TO_SCAN = 1000  # this will include stickied posts, which we are skipping
HOURS = 6
SLEEP_TIME_SECONDS = int(HOURS * 60 * 60)
FLAIR_TEXT = "Top 1% Most Helpful Users of "
MONTHS = [['December', ''], ['January', ''], ['February', ''], ['March', ''], ['April', ''], ['May', ''], ['June', ''],
          ['July', ''], ['August', ''], ['September', ''], ['October', ''], ['November', ''], None]
MONTH_NAME_INDEX = 0
FLAIR_TEMPLATE_ID_INDEX = 1

# ************************************************* GLOBAL VARIABLES ************************************************* #
start_seconds = 0
end_seconds = 0
previous_day = 0


# ************************************************* GLOBAL CONSTANTS ************************************************* #
def edit_flair():
    # only true on the first iteration on the 1st day of the month
    is_new_month = (int(datetime.datetime.today().day) - previous_day) < 0

    totals_arr = []
    ratio_arr = []

    """
    Build an array in this format:
    
        [ [(string) Username, (int) Total Comments, (int) Total Score, (int) Total Negative Comments] ]
    
    I am currently not doing anything useful with the total comments and total score besides calculating the average
    """
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

    totals_arr.sort(reverse=True, key=lambda x: x[1])  # index 1 sorts by average score

    """
    Calculate the top 1% of the number of users in totals_arr and starting with totals_arr sorted by most comments, 
    append each user to ratio_arr, which gives us a list of the most helpful users (see bugs section) ratio_arr is 
    in the format: [[(string) username, (int) average score]]
    """
    top_1_percent = math.ceil(len(totals_arr) * 0.01)  # ceil ensures we always have at least 1 entry in the list
    for i in range(0, top_1_percent):
        if totals_arr[i][3] == 0:  # skip those with a negative top-level comment
            ratio_arr.append([totals_arr[i][0], round((totals_arr[i][2]) / (totals_arr[i][1]), 2)])

    ratio_arr.sort(reverse=True, key=lambda x: x[1])  # index 1 sorts by average score

    if is_new_month:
        prev_month = int(datetime.datetime.today().month) - 1
        get_flair_template_ids()
        """MAKE SURE TO COMMENT OUT THESE LINES WHEN DEBUGGING!!!"""
        SUBREDDIT.flair.delete_all()  # you may or may not want to delete the flair for all users of a subreddit!
        for i in range(0, len(ratio_arr)):
            SUBREDDIT.flair.set(ratio_arr[i][0], flair_template_id=MONTHS[prev_month][FLAIR_TEMPLATE_ID_INDEX])

    edit_wiki(ratio_arr, is_new_month)
    return is_new_month


def get_flair_template_ids():
    missing_months = 0

    for month in MONTHS:
        if month is None:
            break
        found = False
        for template in SUBREDDIT.flair.templates:
            if month[MONTH_NAME_INDEX] in template["text"]:
                month[FLAIR_TEMPLATE_ID_INDEX] = template["id"]
                found = True
                break

        if not found:
            missing_months += 1

    if missing_months > 0:
        # I'm not sure how to handle this yet. This means that the sub must maintain a unique user flair template that
        # contains the matching string for each month. If we don't want to include the name of the month in each flair,
        # then this is all unnecessary.
        print("User Flair template list is missing " + str(missing_months) + " month(s)")


def edit_wiki(ratio_arr, new_month):

    ####################################################################################################################
    # We edit the wiki upon two conditions:
    #
    #   1. After every 6-hour iteration (we do not edit user flair in this case).
    #   2. After the first iteration of the main loop on the 1st day of the month.
    #
    # This will accept Markdown syntax and the Reddit wiki pages will create a TOC based on the tags used. This may be
    # helpful for future needs.
    ####################################################################################################################

    if new_month:
        month_string = MONTHS[int(datetime.datetime.today().month) - 1][MONTH_NAME_INDEX]
        reason_string = month_string + "'s Top 1% update"
        wiki_content = ("Top 1% Most Helpful Users of " + month_string)

        for i in range(0, len(ratio_arr)):
            wiki_content += ("\n\n" + str(i+1) + ". " + ratio_arr[i][0] +
                             " [ average score: " + str(ratio_arr[i][1]) + " ]")

        # this will add a new revision to an existing page, or create the page if it doesn't exist
        SUBREDDIT.wiki[BOT_NAME].edit(content=wiki_content, reason=reason_string)
    else:
        wiki_content = "Last updated (UTC): " + str(datetime.datetime.utcnow())
        reason_string = "6-hour-update"
        for i in range(0, len(ratio_arr)):
            wiki_content += ("\n\n" + str(i+1) + ". " + ratio_arr[i][0] +
                             " [ average score: " + str(ratio_arr[i][1]) + " ]")
        SUBREDDIT.wiki[BOT_NAME + "/" + reason_string].edit(content=wiki_content, reason=reason_string)


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
    # including this as a workaround for the Docker logs, remove when fixed
    print("Sleeping since " + sleep_time + ", waking up in " + str(HOURS) + " hours.")

    for i in range(0, SLEEP_TIME_SECONDS):
        # FIXME this does not print in Docker logs
        # print("\r", "Sleeping since " + sleep_time + ", waking up in " +
        #       str(SLEEP_TIME_SECONDS - i).rjust(5, "0") + " sec", end="")
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
        print("Mod invite accepted from r/" + SUB + ", starting main program.")
    except RedditAPIException:
        print("No pending mod invites from r/" + SUB + ". Assuming the account u/" + BOT_NAME + " is already a mod with"
              " flair and wiki permissions, starting main program.")

    total_comments = 0
    last_total_comments = 0

    while True:
        last_total_comments = total_comments
        time_elapsed = 0
        total_posts = 0
        total_comments = 0

        try:
            with open("stats.json", "r+") as f:
                obj = json.load(f)
                start_seconds = time.perf_counter()

                for submission in SUBREDDIT.hot(limit=NUM_OF_POSTS_TO_SCAN):

                    if submission.stickied is False:
                        total_posts += 1
                        # FIXME this does not print in Docker logs
                        print("\r", "Began scanning submission ID " +
                              str(submission.id) + " at " + time.strftime("%H:%M:%S"), end="")

                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments:
                            if not comment.distinguished:
                                user_id = str(comment.author)
                                total_comments += 1
                                # print("\r", "Total Comments Scanned: " + str(total_comments), end="")
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

            if edit_flair():
                # clear out the comment log at the beginning of each month
                obj["users"] = {}

            try:
                with open("stats.json", "w") as f:
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
        with open("stats.json", "w") as f:
            f.seek(0)
            json.dump(obj, f, indent=2)
    except NameError:
        sys_exit()
    sys_exit()
