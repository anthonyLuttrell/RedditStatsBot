import datetime
import json
import math
import os
import sys
import threading
import time
from queue import Queue
from typing import Any

from Scanner import Scanner
from args import get_args

# ************************************************* GLOBAL CONSTANTS ************************************************* #
MONTHS = [
    ['December', ''],
    ['January', ''],
    ['February', ''],
    ['March', ''],
    ['April', ''],
    ['May', ''],
    ['June', ''],
    ['July', ''],
    ['August', ''],
    ['September', ''],
    ['October', ''],
    ['November', ''],
    None]  # we get the previous month by subtracting 1, so December must be before January.

RUN_TIME = []
ARGS = get_args()
Q_MAX_SIZE = 20
NAME_IDX = 0
FLAIR_TEMPLATE_ID_IDX = 1
TOTAL_COMMENTS_IDX = 1
AVG_SCORE_IDX = 1
TOTAL_SCORE_IDX = 2
NEG_COMMENTS_IDX = 3
NUM_POSTS_TO_SCAN = ARGS.posts
scanner_queue = Queue(maxsize=Q_MAX_SIZE)

alphabet_scanner = Scanner("alphabetbot",
                           "CookingStatsBot",
                           ARGS.posts,
                           30)
cooking_scanner = Scanner("Cooking",
                          "CookingStatsBot",
                          ARGS.posts,
                          30)

scanner_list = [alphabet_scanner, cooking_scanner]


def edit_flair(obj, scanner) -> bool:
    """Deletes and sets user flair, then updates the wiki pages.

    We determine when it is a new month when the previous_day is greater than
    today's day (when 31 rolls back to 1).

    If it is a new month, we delete all current user flair across the entire
    subreddit, then set the new flair based on the results from the most recent
    iteration. We then update the wiki pages.

    :return: is_new_month:
                A bool that is true after the first iteration of the main loop
                on the first day of the month.
    """
    is_new_month = scanner.previous_day > int(datetime.datetime.today().day)
    totals_arr = get_totals_array(obj)
    ratios_arr = get_ratios_array(totals_arr)

    if is_new_month:
        prev_month = int(datetime.datetime.today().month) - 1
        set_flair_template_ids(scanner.sub_instance)

        # this deletes the flair for all users of a subreddit!
        if ARGS.debug is None:
            scanner.sub_instance.flair.delete_all()
            for i in range(0, len(ratios_arr)):
                scanner.sub_instance.flair.set(ratios_arr[i][NAME_IDX],
                                               flair_template_id=MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX])
        else:
            print("Debug output only, no flair has been changed")
            for i in range(0, len(ratios_arr)):
                print("Flair updated for: " + ratios_arr[i][NAME_IDX] + " for " +
                      MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX])

    edit_wiki(ratios_arr, is_new_month, scanner)
    return is_new_month


def get_totals_array(users_obj) -> list:
    """Builds and sorts the totals array.

    Loop through the users_obj, adding up the total number of comments, the
    total score, and the total number of comments with a negative score.

    For example:
        [["bob",31,278,0],["jane",12,773,2]]

    Not currently not doing anything useful with the total comments and total
    score besides calculating the average. There is more potential here.

    :arg users_obj:
            A key-value pair object that contains the user ID, and each comment
            ID and comment score.

    :return totals_arr:
                A list of lists, each sublist consists of the username, that
                user's total number of comments, total score, and total number
                of negative comments. This list is reverse-sorted by the total
                number of comments before it is returned.
    """
    totals_arr = []
    for user in users_obj["users"]:
        total_user_comments = 0
        total_user_score = 0
        total_user_negatives = 0
        for score in users_obj["users"][user]["commentScore"]:
            total_user_comments += 1
            total_user_score += score
            if score < 0:
                total_user_negatives += 1
        totals_arr.append([str(user), int(total_user_comments), int(total_user_score), int(total_user_negatives)])

    totals_arr.sort(reverse=True, key=lambda x: x[TOTAL_COMMENTS_IDX])

    return totals_arr


def get_ratios_array(totals_arr) -> list:
    """
    Calculate the top 1% of the number of users in totals_arr and starting with totals_arr sorted by most comments,
    append each user to ratio_arr, which gives us a list of the most helpful users (see bugs section) ratio_arr is
    in the format: [[(string) username, (int) average score]]
    """
    ratio_arr = []
    top_1_percent = math.ceil(len(totals_arr) * 0.01)  # ceil ensures we always have at least 1 entry in the list
    for i in range(0, top_1_percent):
        if totals_arr[i][NEG_COMMENTS_IDX] == 0:  # skip those with a negative top-level comment
            ratio_arr.append([totals_arr[i][NAME_IDX],
                              round((totals_arr[i][TOTAL_SCORE_IDX]) / (totals_arr[i][TOTAL_COMMENTS_IDX]), 2)])

    ratio_arr.sort(reverse=True, key=lambda x: x[AVG_SCORE_IDX])

    return ratio_arr


def set_flair_template_ids(sub_instance):
    missing_months = 0

    for month in MONTHS:
        if month is None:
            break
        found = False
        for template in sub_instance.flair.templates:
            if month[NAME_IDX] in template["text"]:
                month[FLAIR_TEMPLATE_ID_IDX] = template["id"]
                found = True
                break

        if not found:
            missing_months += 1

    if missing_months > 0:
        # I'm not sure how to handle this yet. This means that the sub must maintain a unique user flair template that
        # contains the matching string for each month. If we don't want to include the name of the month in each flair,
        # then this is all unnecessary.
        print("User Flair template list is missing " + str(missing_months) + " month(s)")


def edit_wiki(ratio_arr, new_month, scanner):
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
        month_string = MONTHS[int(datetime.datetime.today().month) - 1][NAME_IDX]
        reason_string = month_string + "'s Top 1% update"
        wiki_content = ("Top 1% Most Helpful Users of " + month_string)

        for i in range(0, len(ratio_arr)):
            wiki_content += ("\n\n" + str(i + 1) + ". " + ratio_arr[i][0] +
                             " [ average score: " + str(ratio_arr[i][1]) + " ]")

        # this will add a new revision to an existing page, or create the page if it doesn't exist
        if ARGS.debug is None:
            scanner.sub_instance.wiki[scanner.bot_name].edit(content=wiki_content, reason=reason_string)
        else:
            print("Wiki destination: " + scanner.bot_name)
            print(wiki_content)
    else:
        wiki_content = "Last updated (UTC): " + str(datetime.datetime.utcnow())
        reason_string = "6-hour-update"
        for i in range(0, len(ratio_arr)):
            wiki_content += ("\n\n" + str(i + 1) + ". " + ratio_arr[i][0] +
                             " [ average score: " + str(ratio_arr[i][1]) + " ]")
        if ARGS.debug is None:
            scanner.sub_instance.wiki[scanner.bot_name + "/" + reason_string].edit(content=wiki_content,
                                                                                   reason=reason_string)
        else:
            print("Wiki destination: " + scanner.bot_name + "/" + reason_string)
            print(wiki_content)


def user_exists(obj, user_id_to_check):
    found = False
    for user in obj["users"]:
        if user_id_to_check == user:
            found = True
            break
    return found


def update_existing(obj, comment_to_update, user_id: str):
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


def add_new(obj, comment_to_add):
    obj["users"][str(comment_to_add.author)] = {"commentId": [comment_to_add.id],
                                                "commentScore": [comment_to_add.score]}


def sleep(scanner):
    sleep_string = time.strftime("%H:%M:%S")
    # including this as a workaround for the Docker logs, remove when fixed
    # print("Sleeping since " + sleep_time + ", waking up in " + str(scanner.get_time_slice()) + " hours.")
    sleep_time_seconds = round(scanner.sleep_seconds - (get_avg_runtime_minutes() * 60))
    for i in range(0, sleep_time_seconds):
        # FIXME this does not print in Docker logs. Just replace it with time.sleep(sleep_time_seconds) if needed
        print("\r", "Sleeping since " + sleep_string + ", waking up in " +
              str(sleep_time_seconds - i).rjust(5, "0") + " sec", end="")
        time.sleep(1)


def sys_exit():
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))


def create_file(file_name):
    # create the files if they don't exist
    try:
        if os.path.isfile(file_name):
            print(file_name + " already exists")
        else:
            with open(file_name, "a") as f:
                f.write("{\"users\":{}}")
                print(file_name + " was created")
    except OSError:
        print("Unable to create new file, terminating program")
        sys_exit()


def fill_scanner_queue():
    for scanner in scanner_list:
        scanner_queue.put(scanner)


def scanner_worker():

    while True:
        minutes_elapsed = 0
        total_posts = 0
        total_comments = 0
        scanner = scanner_queue.get()
        print(f"\nWorking on {scanner}, for {scanner.sub_name}")

        try:
            file_name = scanner.sub_name + ".json"
            create_file(file_name)

            with open(scanner.sub_name + ".json", "r+") as f:
                obj = json.load(f)
                start_seconds = time.perf_counter()

                for submission in scanner.sub_instance.hot(limit=scanner.num_posts_to_scan):

                    # scan each post from the top down when sorted by "hot"
                    if submission.stickied is False:
                        total_posts += 1
                        submission.comments.replace_more(limit=0)

                        for comment in submission.comments:
                            # scan each top-level comment
                            if not comment.distinguished:
                                user_id = str(comment.author)
                                total_comments += 1
                                # FIXME this does not print in Docker logs
                                print("\r", "Began scanning submission ID " + str(submission.id) +
                                      ", total Comments Scanned: " +
                                      str(total_comments), end="")
                                if user_id != "None":
                                    if user_exists(obj, user_id):
                                        update_existing(obj, comment, user_id)
                                    else:
                                        add_new(obj, comment)
                            time.sleep(0.1)  # avoids HTTP 429 errors

                    time.sleep(0.1)  # avoids HTTP 429 errors

                # DONE scanning
            minutes_elapsed += (time.perf_counter() - start_seconds) / 60
            update_avg_runtime(minutes_elapsed)
            print("\nTime elapsed: " + str(datetime.timedelta(minutes=minutes_elapsed)))

            if edit_flair(obj, scanner):
                # clear out the comment log at the beginning of each month
                obj["users"] = {}

            try:
                with open(scanner.sub_name + ".json", "w") as f:
                    f.seek(0)
                    json.dump(obj, f, indent=2)
                scanner.previous_day = datetime.datetime.today().day
            except FileNotFoundError:
                print("File Not Found, exiting.")
                sys_exit()

        except (KeyboardInterrupt, SystemExit):
            # catches Ctrl+C and IDE program interruption to ensure we write to the json file
            # FIXME using threads here is causing more complications. When stopping the program now, KeyboardInterrupt
            #  is not caught here, so we do not close out the json file like we should. There does not appear to be an
            #  easy fix for this. Though, switching to a database instead of local files will make this meaningless.
            try:
                print("\n-- Process halted, dumping JSON file --")
                # highly unlikely that this scanner will be referenced before it is assigned
                with open(scanner.sub_name + ".json", "w") as f:
                    f.seek(0)
                    json.dump(obj, f, indent=2)
            except NameError:
                sys_exit()
            sys_exit()

        print(f"Finished working on {scanner}, for {scanner.sub_name}")
        sleep(scanner)

        # ensures the queue is never empty
        scanner_queue.put(scanner)

        scanner_queue.task_done()


def update_avg_runtime(minutes):
    RUN_TIME.append(minutes)


def get_avg_runtime_minutes():
    return 0 if len(RUN_TIME) == 0 else sum(RUN_TIME) / len(RUN_TIME)


def main():
    fill_scanner_queue()

    # daemon=True here means the worker thread will stop to run even when the queue is empty
    threading.Thread(target=scanner_worker, daemon=True).start()

    # Blocks succeeding code until all items in the Queue have been gotten (removed) and marked with task_done
    scanner_queue.join()

    print(time.strftime("%H:%M:%S"), "Something went wrong, the queue was empty when it should not have been. Exiting.")


if __name__ == "__main__":
    main()
