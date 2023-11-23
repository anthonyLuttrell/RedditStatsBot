import datetime
import json
import math
import os
import sys
import time

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

ARGS = get_args()
NAME_IDX = 0
FLAIR_TEMPLATE_ID_IDX = 1
TOTAL_COMMENTS_IDX = 1
AVG_SCORE_IDX = 1
TOTAL_SCORE_IDX = 2
NEG_COMMENTS_IDX = 3
NUM_POSTS_TO_SCAN = 1000
SLEEP_TIME_SECONDS = 21600  # 6 hours
DEBUG_POSTS_TO_SCAN = ARGS.posts
DEBUG_SLEEP_TIME = 30
scanner_list = []

if ARGS.debug is not None:
    alphabet_scanner = Scanner("alphabetbot",
                               "CookingStatsBot",
                               DEBUG_POSTS_TO_SCAN,
                               DEBUG_SLEEP_TIME)
    cooking_scanner = Scanner("Cooking",
                              "CookingStatsBot",
                              DEBUG_POSTS_TO_SCAN,
                              DEBUG_SLEEP_TIME)
    scanner_list.append(alphabet_scanner)
    scanner_list.append(cooking_scanner)
else:
    cooking_scanner = Scanner("Cooking",
                              "CookingStatsBot",
                              NUM_POSTS_TO_SCAN,
                              SLEEP_TIME_SECONDS)
    scanner_list.append(cooking_scanner)


def edit_flair(obj: str, scanner: Scanner) -> bool:
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


def sleep(scanner: Scanner):
    """Puts the program to sleep for a calculated amount of time.

    We want each scanner to run four times per day, so that means it must complete one iteration every six hours
    (24 / 4 = 6). We must consider the runtime for each scanner to ensure each scanner can finish within this six-hour
    window. To calculate the sleep time for each scanner, we start with six hours and subtract its average runtime, and
    then subtract the total cumulative average runtime for all scanners. For example:

    Scanner 1 average runtime =  900 seconds
    Scanner 2 average runtime = 2268 seconds
    Scanner 3 average runtime = 2088 seconds

    total cumulative runtime = 5256 seconds
    average total cumulative runtime = (5256 / 3) = 1752 seconds

    Scanner 1 sleep time = (21600 -  900 - 1752) = 18948 seconds (5.26 hours)
    Scanner 2 sleep time = (21600 - 2268 - 1752) = 17580 seconds (4.88 hours)
    Scanner 2 sleep time = (21600 - 2088 - 1752) = 17760 seconds (4.93 hours)

    Args:
        scanner: The Scanner object that we want to put to sleep after it has completed one iteration.

    """
    sleep_string = time.strftime("%H:%M:%S")
    first_pass_done = True
    cumulative_avg_runtime = 0
    for temp_scanner in scanner_list:
        avg_runtime = temp_scanner.get_avg_runtime_seconds()
        if avg_runtime == 0:
            # if any of the averages are 0 that means the scanner has NOT completed an iteration yet
            first_pass_done = False
        cumulative_avg_runtime += avg_runtime

    # this allows each scanner to run to completion before we use cumulative_avg_runtime
    runtime = cumulative_avg_runtime / len(scanner_list)
    individual_avg_runtime = runtime if first_pass_done else scanner.get_avg_runtime_seconds()

    # when scanner.sleep_seconds is very small (when debugging), this can be negative, so we'll just set it to 1
    sleep_sec = round(scanner.sleep_seconds - scanner.get_avg_runtime_seconds() - cumulative_avg_runtime)
    sleep_time_seconds = 1 if sleep_sec < 0 else sleep_sec

    max_scanners = cumulative_avg_runtime / individual_avg_runtime

    if len(scanner_list) > max_scanners and first_pass_done:
        print(f"You have exceeded the recommended number of scanners: {max_scanners}, "
              f"currently using {len(scanner_list)} scanners. "
              f"Some scanners may not finish within {SLEEP_TIME_SECONDS / 60 / 60} hours!")

    print(f"Sleeping since {sleep_string}, waking up in {str(round(sleep_time_seconds / 60 / 60, 2))} hours.")
    time.sleep(sleep_time_seconds)


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


def main():

    while True:
        try:
            for scanner in scanner_list:
                seconds_elapsed = 0
                total_posts = 0
                total_comments = 0
                file_name = scanner.sub_name + ".json"
                create_file(file_name)

                # we don't need a try/catch here because create_file guarantees the file exists
                with open(file_name, "r+") as f:
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

                            # DONE scanning all comments in post

                        time.sleep(0.1)  # avoids HTTP 429 errors

                # DONE scanning all posts in subreddit, moving on to next scanner in the list, but first...
                seconds_elapsed += time.perf_counter() - start_seconds
                scanner.append_avg_runtime_seconds(seconds_elapsed)
                print("\nTime elapsed: " + str(datetime.timedelta(minutes=(seconds_elapsed / 60))))
                scanner.previous_day = datetime.datetime.today().day  # update current day before we go to edit_flair

                if edit_flair(obj, scanner):
                    # clear out the comment log at the beginning of each month
                    obj["users"] = {}

                try:
                    # write to the JSON file and close the file
                    with open(file_name, "w") as f:
                        f.seek(0)
                        json.dump(obj, f, indent=2)
                    sleep(scanner)
                except FileNotFoundError:
                    print("File Not Found, exiting.")
                    sys_exit()

            # END for-each scanner loop
        except (KeyboardInterrupt, SystemExit):
            # catches Ctrl+C and IDE program interruption to ensure we write to the json file
            try:
                print("\n-- Process halted, dumping JSON file --")
                # highly unlikely that file_name is referenced before it is defined
                with open(file_name, "w") as f:
                    f.seek(0)
                    json.dump(obj, f, indent=2)
            except NameError:
                sys_exit()
            sys_exit()
    # END main while loop


if __name__ == "__main__":
    main()
