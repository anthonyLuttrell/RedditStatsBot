import datetime
import json
import math
import os
import sys
import time
from typing import List
import praw.models
import prawcore.exceptions

from Scanner import Scanner
from args import get_args
from ftp import send_file

# TODO implement a read-only mode
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
NUM_POSTS_TO_SCAN = 100
SLEEP_TIME_SECONDS = 600  # 6 hours 21600
DEBUG_POSTS_TO_SCAN = ARGS.posts
DEBUG_SLEEP_TIME = 30
scanner_list = []

if ARGS.debug is not None:
    alphabet_scanner = Scanner("alphabetbot",
                               "CookingStatsBot",
                               DEBUG_POSTS_TO_SCAN,
                               DEBUG_SLEEP_TIME)
    # cooking_scanner = Scanner("Cooking",
    #                           "CookingStatsBot",
    #                           DEBUG_POSTS_TO_SCAN,
    #                           DEBUG_SLEEP_TIME)
    scanner_list.append(alphabet_scanner)
    # scanner_list.append(cooking_scanner)
else:
    # cooking_scanner = Scanner("Cooking",
    #                           "CookingStatsBot",
    #                           NUM_POSTS_TO_SCAN,
    #                           SLEEP_TIME_SECONDS)
    learnpython_scanner = Scanner("learnpython",
                                  "CookingStatsBot",
                                  NUM_POSTS_TO_SCAN,
                                  SLEEP_TIME_SECONDS)
    askculinary_scanner = Scanner("AskCulinary",
                                  "CookingStatsBot",
                                  NUM_POSTS_TO_SCAN,
                                  SLEEP_TIME_SECONDS)
    cookingforbeginners_scanner = Scanner("cookingforbeginners",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    askbaking_scanner = Scanner("askbaking",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    baking_scanner = Scanner("baking",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    breadit_scanner = Scanner("breadit",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    askmen_scanner = Scanner("askmen",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    learnprogramming_scanner = Scanner("learnprogramming",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    funny_scanner = Scanner("funny",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    chicago_scanner = Scanner("chicago",
                                          "CookingStatsBot",
                                          NUM_POSTS_TO_SCAN,
                                          SLEEP_TIME_SECONDS)
    scanner_list.append(learnpython_scanner)
    scanner_list.append(askculinary_scanner)
    scanner_list.append(askbaking_scanner)
    scanner_list.append(baking_scanner)
    scanner_list.append(breadit_scanner)
    scanner_list.append(askmen_scanner)
    scanner_list.append(learnprogramming_scanner)
    scanner_list.append(funny_scanner)
    scanner_list.append(chicago_scanner)
    # scanner_list.append(cooking_scanner)


def edit_flair(obj, scanner: Scanner) -> bool:
    """Deletes and sets user flair, then updates the wiki pages.

    We determine when it is a new month when the previous_day is greater than today's day (when 31 rolls back to 1). If
    it is a new month, we delete all current user flair across the entire subreddit, then set the new flair based on the
    results from the most recent iteration. We then update the wiki.

    Args:
      obj:
        A json-syntax object that contains an entry for each user, along with that user's comment IDs and scores.
      scanner:
        The Scanner object that we are currently working on.

    Returns:
      is_new_month:
        A bool that is true after the first iteration of the main loop on the first day of the month.
    """
    is_new_month = scanner.previous_day > int(datetime.datetime.today().day)
    totals_arr = get_totals_array(obj)
    ratios_arr = get_ratios_array(totals_arr)

    if is_new_month and scanner.is_mod:
        prev_month = int(datetime.datetime.today().month) - 1
        set_flair_template_ids(scanner.sub_instance)

        if ARGS.debug is None:
            # this deletes the flair for all users of a subreddit!
            scanner.sub_instance.flair.delete_all()
            for i in range(0, len(ratios_arr)):
                scanner.sub_instance.flair.set(ratios_arr[i][NAME_IDX],
                                               flair_template_id=MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX])
        else:
            print("Debug output only, no flair has been changed")
            for i in range(0, len(ratios_arr)):
                print("Flair updated for: " +
                      ratios_arr[i][NAME_IDX] +
                      " for " +
                      MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX])

    edit_wiki(ratios_arr, is_new_month, scanner)
    return is_new_month


def get_totals_array(users_obj) -> List[list]:
    """Builds and sorts the totals array.

    Loop through the users_obj, adding up the total number of comments, the total score, and the total number of
    comments with a negative score.

    For example: [["bob",31,278,0],["jane",12,773,2]]

    Not currently not doing anything useful with the total comments and total score besides calculating the average.
    There is more potential here.

    Args:
      users_obj:
        A key-value pair object that contains the user ID, and each comment ID and comment score.

    Returns:
      totals_arr:
        A list of lists, each sublist consists of the username, that user's total number of comments, total score, and
        total number of negative comments. This list is reverse-sorted by the total number of comments before it is
        returned.
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


def get_ratios_array(totals_arr: List[list]) -> List[list]:
    """ Returns most helpful users.

    Calculate the top 1% of the number of users in totals_arr and starting with totals_arr sorted by most comments,
    append each user to ratio_arr, which gives us a list of the most helpful users (see bugs section) ratio_arr is in
    the format: [[(string) username, (int) average score]]

    Args:
        totals_arr: A list of lists containing user information.

    Returns:
        A list of lists, where each inner list contains the username and average
        score for a user.
    """
    # TODO Find the top 1% highest number of total comments,
    #  then calculate the percentage of negative comments from these comments,
    #  then find the top 1% of that.
    ratio_arr = []
    top_1_percent = math.ceil(len(totals_arr) * 0.01)  # ceil ensures we always have at least 1 entry in the list
    for i in range(0, top_1_percent):
        if totals_arr[i][NEG_COMMENTS_IDX] == 0:  # skip those with a negative top-level comment
            ratio_arr.append([totals_arr[i][NAME_IDX],
                              round((totals_arr[i][TOTAL_SCORE_IDX]) / (totals_arr[i][TOTAL_COMMENTS_IDX]), 2)])

    ratio_arr.sort(reverse=True, key=lambda x: x[AVG_SCORE_IDX])

    return ratio_arr


def set_flair_template_ids(sub_instance) -> None:
    """Assigns a user flair template ID to the corresponding month in the MONTHS list.

    Each subreddit must maintain a unique user flair template that contains the matching string for each month. If we
    don't want to include the name of the month in each flair, then this is all unnecessary. If there is no matching
    user flair template, then no user flair will be applied.

    Args:
      sub_instance:
        The PRAW subreddit instance to search.

    Returns:
        None.
    """
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
        print(f"User Flair template list is missing {str(missing_months)} month(s)")


def edit_wiki(ratio_arr: list, new_month: bool, scanner: Scanner) -> None:
    """Edit the subreddit's wiki page.

    The wiki page is edited under two conditions:
      1. After every 6-hour iteration (user flair is not edited in this case).
      2. After the first iteration of the main loop on the 1st day of the month.

    Note:
        This will accept Markdown syntax and the Reddit wiki pages will create a TOC based on the tags used. This may be
        helpful for future needs.

    Args:
        ratio_arr: A list of lists containing the username and average score for each user.
        new_month: A boolean indicating whether it is the first iteration of the main loop on the 1st day of the month.
        scanner: The Scanner object that we are currently working on.

    Returns:
        None.
    """
    if new_month:
        month_string = MONTHS[int(datetime.datetime.today().month) - 1][NAME_IDX]
        reason_string = month_string + "'s Top 1% update"
        wiki_content = ("Top 1% Most Helpful Users of " + month_string)

        for i in range(0, len(ratio_arr)):
            wiki_content += f"\n\n{str(i + 1)}. {ratio_arr[i][0]} [ average score: {str(ratio_arr[i][1])} ]"

        # this will add a new revision to an existing page, or create the page if it doesn't exist
        if ARGS.debug is None and scanner.is_mod:
            try:
                scanner.sub_instance.wiki[scanner.bot_name].edit(content=wiki_content, reason=reason_string)
            except prawcore.exceptions.NotFound as e:
                print(f"{e}: Could not edit Wiki page on {scanner.sub_name}, does {scanner.bot_name} have wiki edit permissions?")
        else:
            # print("Wiki destination: " + scanner.bot_name)
            # print(wiki_content)
            pass
    else:
        trimmed_timestamp = datetime.datetime.utcnow()
        trimmed_timestamp.replace(microsecond=round(trimmed_timestamp.microsecond, -3))
        wiki_content = "Last updated (UTC): " + str(trimmed_timestamp)
        reason_string = "6-hour-update"
        for i in range(0, len(ratio_arr)):
            # FIXME some duplicate code here we can get rid of
            wiki_content += f"\n\n{str(i + 1)}. {ratio_arr[i][0]} [ average score: {str(ratio_arr[i][1])} ]"
        if ARGS.debug is None and scanner.is_mod:
            try:
                scanner.sub_instance.wiki[scanner.bot_name + "/" + reason_string].edit(content=wiki_content,
                                                                                   reason=reason_string)
            except prawcore.exceptions.NotFound as e:
                print(f"{e}: Could not edit Wiki page on {scanner.sub_name}")
        else:
            # print("Wiki destination: " + scanner.bot_name + "/" + reason_string)
            # print(wiki_content)
            pass


def upload_file_to_ftp_server(file_name):
    try:
        send_file(file_name)
    except:
        print("Unable to upload file")


def user_exists(obj: dict, user_id_to_check: str) -> bool:
    """Check if a user with the given ID exists in the 'obj' dictionary.

    Args:
      obj: A dictionary that represents all user with their comment IDs and scores.
      user_id_to_check: The ID of the user to check.

    Returns:
      True if a user with the given ID exists, False otherwise.
    """
    for user in obj["users"]:
        if user_id_to_check == user:
            return True
    return False


def update_existing(obj: dict, comment_to_update: praw.models.Comment, user_id: str) -> None:
    """Update comment score if comment exist else add new comments.

    The function checks if the comment ID already exists in the 'commentId' list of the user. If the comment ID exists,
    the score is updated in the corresponding position of the 'commentScore' list. If the comment ID does not exist, the
    comment ID and score are added to the respective lists.

    Args:
      obj: A dictionary that represents all user with their comment IDs and scores.
      comment_to_update: The PRAW comment object to update.
      user_id: The User ID for whom the comment belongs to.

    Returns:
      None.
    """
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


def add_new(obj: dict, comment_to_add: praw.models.Comment) -> None:
    """Add a new comment to the 'obj' dictionary.

    The function creates a new entry in the 'users' dictionary with the author's username as the key. The 'commentId'
    list is initialized with the ID of the given comment, and the 'commentScore' list is initialized with the score of
    the given comment.

    Args:
      obj: A dictionary that represents all user with their comment IDs and scores.
      comment_to_add: The PRAW comment object to add.

    Returns:
      None.
    """
    obj["users"][str(comment_to_add.author)] = {"commentId": [comment_to_add.id],
                                                "commentScore": [comment_to_add.score]}


def sleep(scanner: Scanner) -> None:
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

    Returns:
      None.
    """
    # FIXME the sleep time is 0.0 hours when you run the scanner with a 1-hour sleep time
    sleep_string = time.strftime("%H:%M:%S")
    date_time = datetime.datetime.now()
    date_time.replace(microsecond=round(date_time.microsecond, -3))
    first_pass_done = True
    cumulative_avg_runtime = 0
    for temp_scanner in scanner_list:
        avg_runtime = temp_scanner.get_avg_runtime_seconds()
        if avg_runtime == 0:
            # Each scanner keeps an array of average runtimes. If any of the
            # averages are 0, that means that scanner has NOT completed a scan.
            first_pass_done = False
        cumulative_avg_runtime += avg_runtime

    # this allows each scanner to run to completion before we use cumulative_avg_runtime
    runtime = cumulative_avg_runtime / len(scanner_list)
    individual_avg_runtime = runtime if first_pass_done else scanner.get_avg_runtime_seconds()

    # There should be no sleep time between scanners until all have completed
    # their first scan. Also, when scanner.sleep_seconds is very small (when
    # debugging), this can be negative, so we set it to 1 for both of these.
    sleep_sec = round(scanner.sleep_seconds - scanner.get_avg_runtime_seconds() - cumulative_avg_runtime)
    sleep_time_seconds = 1 if sleep_sec < 0 or not first_pass_done else sleep_sec

    max_scanners = cumulative_avg_runtime / individual_avg_runtime

    if len(scanner_list) > max_scanners and first_pass_done:
        print(f"You have exceeded the recommended number of scanners: {max_scanners},\n currently using {len(scanner_list)} scanners.\n Some scanners may not finish within {SLEEP_TIME_SECONDS / 60 / 60} hours!")
    # TODO can we provide a more accurate wake time here?
    sleep_time_string = date_time + datetime.timedelta(seconds=sleep_time_seconds)
    print(f"Sleeping since {sleep_string}, waking up at {str(sleep_time_string.time())}")
    time.sleep(sleep_time_seconds)


def sys_exit():
    """Performs a graceful program termination for Windows and Linux systems.

    Args:
      None.

    Returns:
      None.
    """
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))


def create_file(file_name: str, debug_ftp: bool, content: str):
    """Creates the files if they don't exist.

    Args:
      file_name: The name of the json file, should match the sub's name.
      debug_ftp: True if you are sending a test file to the FTP server.
      content: A JSON-syntax string that will fill the file.

    Returns:
      None.
    """
    try:
        if os.path.isfile(file_name):
            print(file_name + " already exists")
        else:
            with open(file_name, "a") as f:
                if debug_ftp:
                    f.write(
                        "{\"users\":{\"96dpi\":{\"commentId\":[\"asdfqwer\",\"jhkjer8f\"],\"commentScore\":[12, 1]}}}")
                else:
                    f.write(content)
                print(file_name + " was created")
    except OSError:
        print("Unable to create new file, terminating program")
        sys_exit()


def main():
    sub_list = {"subs": []}
    for scanner in scanner_list:
        sub_list["subs"].append(scanner.sub_name)
    json_sub_list = json.dumps(sub_list)
    create_file("subreddits.json", False, str(json_sub_list))
    send_file("subreddits.json")
    while True:
        try:
            for scanner in scanner_list:
                seconds_elapsed = 0
                total_posts = 0
                total_comments = 0
                file_name = scanner.sub_name + ".json"
                create_file(file_name, False, "{\"users\":{},\"timestamp\":[]}")

                # we don't need a try/catch here because create_file guarantees the file exists
                with open(file_name, "r+") as f:
                    obj = json.load(f)
                    start_seconds = time.perf_counter()

                    try:
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
                        trimmed_timestamp = datetime.datetime.utcnow()
                        trimmed_timestamp.replace(microsecond=round(trimmed_timestamp.microsecond, -3))
                        obj["timestamp"] = str(trimmed_timestamp)
                    except prawcore.exceptions.ServerError as e:
                        # this will catch HTTP server errors from Reddit's servers
                        print(e)

                # DONE scanning all posts in subreddit, moving on to next scanner in the list, but first...
                seconds_elapsed += time.perf_counter() - start_seconds
                scanner.append_avg_runtime_seconds(seconds_elapsed)
                print("\nTime elapsed: " + str(datetime.timedelta(minutes=(seconds_elapsed / 60))))

                # update current day before we go to edit_flair
                scanner.previous_day = ARGS.day if ARGS.day > 0 else datetime.datetime.today().day

                if edit_flair(obj, scanner):
                    # clear out the comment log at the beginning of each month
                    obj["users"] = {}

                try:
                    # write to the JSON file and close the file
                    with open(file_name, "w") as f:
                        f.seek(0)
                        json.dump(obj, f, indent=2)
                    upload_file_to_ftp_server(file_name)
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
    # create_file("test_file.json", True, "")
    # send_file("test_file.json")
