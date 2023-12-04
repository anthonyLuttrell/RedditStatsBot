import praw.models
import prawcore.exceptions
import datetime
import json
import math
import os
import sys
import time
import ftp
import scanner_pool
import log
from typing import List
from Scanner import Scanner
from args import get_args

# ************************************************* GLOBAL CONSTANTS ************************************************* #
# We get the previous month by subtracting 1, so December must be before
# January, and the 12th month must be None, so we can reference November.
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
    None]

ARGS = get_args()
NAME_IDX = 0
FLAIR_TEMPLATE_ID_IDX = 1
TOTAL_COMMENTS_IDX = 1
AVG_SCORE_IDX = 1
TOTAL_SCORE_IDX = 2
NEG_COMMENTS_IDX = 3
SUBS_FILENAME = "subreddits.json"
DEBUG_FILENAME = "debug.log"


def edit_flair(obj: dict, scanner: Scanner) -> None:
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
    totals_arr = get_totals_array(obj)
    ratios_arr = get_ratios_array(totals_arr)
    prev_month = int(datetime.datetime.today().month) - 1
    set_flair_template_ids(scanner.sub_instance)

    if ARGS.debug is None:
        # this deletes the flair for all users of a subreddit!
        # these operations can take several seconds to complete
        scanner.sub_instance.flair.delete_all()
        for i in range(0, len(ratios_arr)):
            scanner.sub_instance.flair.set(
                ratios_arr[i][NAME_IDX],
                flair_template_id=MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX]
            )
    else:
        log.debug("Debug output only, no flair has been changed")
        for i in range(0, len(ratios_arr)):
            log.debug("Flair updated for: ",
                      ratios_arr[i][NAME_IDX],
                      " for ",
                      MONTHS[prev_month][FLAIR_TEMPLATE_ID_IDX])

    # clear out the comment log and debug log at the beginning of each month
    obj["users"] = {}
    open(DEBUG_FILENAME, "w").close()


def get_totals_array(users_obj: dict) -> List[list]:
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


def set_flair_template_ids(sub_instance: praw.models.Subreddit) -> None:
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
        # TODO this should print the exact months that are missing
        log.warn("User Flair template list is missing ", str(missing_months), " month(s)")


def edit_wiki(ratio_arr: list, scanner: Scanner) -> None:
    """Edit the subreddit's wiki page.

    The wiki page is edited under two conditions:
      1. After every 6-hour iteration (user flair is not edited in this case).
      2. After the first iteration of the main loop on the 1st day of the month.

    Note:
        This will accept Markdown syntax and the Reddit wiki pages will create a TOC based on the tags used. This may be
        helpful for future needs.

    Args:
        ratio_arr: A list of lists containing the username and average score for each user.
        scanner: The Scanner object that we are currently working on.

    Returns:
        None.
    """
    trimmed_timestamp = datetime.datetime.utcnow()
    # FIXME I don't think this is actually doing anything
    trimmed_timestamp.replace(microsecond=round(trimmed_timestamp.microsecond, -3))
    wiki_content = "Last updated (UTC): " + str(trimmed_timestamp)
    reason_string = "6-hour-update"
    for i in range(0, len(ratio_arr)):
        wiki_content += f"\n\n{str(i + 1)}. {ratio_arr[i][0]} [ average score: {str(ratio_arr[i][1])} ]"
    if ARGS.debug is None and scanner.is_mod:
        try:
            scanner.sub_instance.wiki[
                scanner.bot_name +
                "/" +
                reason_string
                ].edit(content=wiki_content, reason=reason_string)
        except prawcore.exceptions.NotFound as e:
            log.error(str(e), ": Could not edit Wiki page on ", scanner.sub_name)


def upload_file_to_ftp_server(file_name: str) -> None:
    try:
        result = ftp.send_file(file_name)
        log.debug(str(result))
    except (Exception,) as e:
        log.error(str(e), ": Unable to upload file")


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

    We want each scanner to run four times per day, so that means it must complete one iteration every six hours. We
    must consider the average runtime for all scanners to ensure each scanner can finish within this six-hour window. To
    calculate the sleep time for each scanner, we start with 6 hours and subtract the cumulative average runtime of all
    scanners. For example:

    Scanner 1 average runtime =  900 seconds
    Scanner 2 average runtime = 2268 seconds
    Scanner 3 average runtime = 2088 seconds

    cumulative average runtime of all scanners = 5256 seconds

    Scanner 1 sleep time = (21600 - 5256) = 16344 seconds (4.54 hours)
    Scanner 2 sleep time = (21600 - 2268) = 19332 seconds (5.37 hours)
    Scanner 2 sleep time = (21600 - 2088) = 19512 seconds (5.42 hours)

    The higher the cumulative average runtime gets, the lower the sleep time gets. The closer it gets to 0, the less
    likely it is for each scanner to finish one loop every 6 hours.

    Args:
      scanner: The Scanner object that we want to put to sleep after it has completed one iteration.

    Returns:
      None.
    """
    sleep_string = time.strftime("%H:%M:%S")
    date_time = datetime.datetime.now()
    sleep_time_seconds = 1
    """
    `sleep_time_seconds` should be `1` in two cases: 
         1.  Until every scanner has completed one pass.
         2.  If the cumulative average runtimes is greater than the supplied scanner's interval. 
    
    If the `adjusted_scanner_interval` is still negative after each scanner has 
    finished one pass, scanners will take longer than `scanner.interval_seconds` 
    to complete each pass, and we should print a warning.
    """
    adjusted_scanner_interval = scanner_pool.get_cumulative_avg_runtime() - get_variance(scanner)

    if adjusted_scanner_interval >= scanner.interval_seconds and scanner_pool.first_pass_completed():
        log.warn("Some scanners may not finish within ",
                 str(round(scanner.interval_seconds / 60 / 60, 2)),
                 " hours!")
    elif scanner_pool.first_pass_completed():
        sleep_time_seconds = adjusted_scanner_interval

    log.info("Cumulative average runtime = ", str(round(scanner_pool.get_cumulative_avg_runtime())))
    log.info(" Current scanner's runtime = ", str(round(scanner.individual_avg_runtime_seconds[-1], 2)))
    log.info("                  Variance = ", str(round(get_variance(scanner), 2)))

    sleep_time_string = date_time + datetime.timedelta(seconds=sleep_time_seconds)
    log.info(f" Now sleeping, waking up at: {str(sleep_time_string.time())}")
    upload_file_to_ftp_server(DEBUG_FILENAME)

    time.sleep(sleep_time_seconds)


def get_variance(scanner: Scanner) -> float:
    """Returns the variance between all the average scanner runtimes."""
    vari_min = min(scanner_pool.cumulative_avg_runtime_list)
    vari_max = max(scanner_pool.cumulative_avg_runtime_list)
    vari_avg = sum(scanner_pool.cumulative_avg_runtime_list) / len(scanner_pool.cumulative_avg_runtime_list)
    vari_dif = vari_max - vari_min
    vari_pct = vari_dif / vari_avg
    return scanner.individual_avg_runtime_seconds[-1] * vari_pct


def sys_exit() -> None:
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


def create_file(file_name: str, content: str) -> None:
    """Creates the files if they don't exist.

    Args:
      file_name: 
        The name of the json file, should match the sub's name.
      content: 
        A JSON-syntax string that will fill the file.

    Returns:
      None.
    """
    try:
        if os.path.isfile(ftp.LOCAL_JSON_DIR + file_name):
            log.debug(file_name, " already exists")
        else:
            with open(ftp.LOCAL_JSON_DIR + file_name, "a") as f:
                f.write(content)
                log.debug(file_name, " was created")
    except OSError:
        log.critical("Unable to create new file, terminating program")
        sys_exit()


def build_subreddit_list(scanner_list) -> None:
    sub_list = {"subs": []}
    temp_sub_list = []

    for scanner in scanner_list:
        temp_sub_list.append(scanner.sub_name)

    temp_sub_list.sort(key=str.lower)
    sub_list["subs"] = temp_sub_list
    json_sub_list = json.dumps(sub_list)
    create_file(SUBS_FILENAME, str(json_sub_list))
    upload_file_to_ftp_server(SUBS_FILENAME)


def is_new_month(previous_day) -> bool:
    return previous_day > int(datetime.datetime.today().day)


def main_scanner_loop() -> None:
    scanner_list = scanner_pool.get_scanner_list()
    build_subreddit_list(scanner_list)
    while True:
        try:
            for scanner in scanner_list:
                log.info("    Now scanning subreddit = ", scanner.sub_name)
                seconds_elapsed = 0
                total_posts = 0
                total_comments = 0
                file_name = scanner.sub_name + ".json"
                create_file(file_name, "{\"users\":{},\"timestamp\":[]}")

                # we don't need a try/catch here because create_file guarantees the file exists
                with open(ftp.LOCAL_JSON_DIR + file_name, "r+") as f:
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
                                        # FIXME this does not print in Docker logs. Do we want something printing every
                                        #  second in the Docker logs? I don't think that's what they are intended for.
                                        if ARGS.debug is not None:
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
                        log.error(str(e))

                # DONE scanning all posts in subreddit, moving on to next scanner in the list, but first...
                seconds_elapsed += time.perf_counter() - start_seconds
                scanner.append_avg_runtime_seconds(seconds_elapsed)
                scanner.first_pass_done = True

                log.info("       Total posts scanned = ", str(total_posts))
                log.info("    Total comments scanned = ", str(total_comments))

                if is_new_month(scanner.previous_day) and scanner.is_mod:
                    edit_flair(obj, scanner)

                # edit the wiki pages after every scanner finishes (every 6 hours)
                edit_wiki(get_ratios_array(get_totals_array(obj)), scanner)

                # update current day after `edit_flair` and before `sleep`
                scanner.previous_day = ARGS.day if ARGS.day > 0 else datetime.datetime.today().day

                try:
                    # write to the JSON file and close the file
                    with open(ftp.LOCAL_JSON_DIR + file_name, "w") as f:
                        f.seek(0)
                        json.dump(obj, f, indent=2)
                    upload_file_to_ftp_server(file_name)
                    sleep(scanner)
                except FileNotFoundError:
                    log.critical("File Not Found, moving to next scanner.")
                    sys_exit()

            # END for-each scanner loop
        except (KeyboardInterrupt, SystemExit):
            # catches Ctrl+C and IDE program interruption to ensure we write to the json file
            try:
                log.warn(" -- Process halted, dumping JSON file --\n")
                # highly unlikely that file_name is referenced before it is defined
                with open(ftp.LOCAL_JSON_DIR + file_name, "w") as f:
                    f.seek(0)
                    json.dump(obj, f, indent=2)
            except NameError:
                sys_exit()
            sys_exit()
    # END main scanner loop


if __name__ == "__main__":
    scanner_pool.build_scanner_list()
    main_scanner_loop()
