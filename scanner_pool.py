from typing import List
from args import get_args
from Scanner import Scanner

ARGS = get_args()
NUM_POSTS_TO_SCAN = ARGS.posts
# must be larger than the cumulative average runtime
SCANNER_INTERVAL_SEC = ARGS.interval
scanner_list = []
cumulative_avg_runtime_list = []

# Subreddits added to this list will be automatically added to the list of scanners.
subreddit_list = [
    "cooking",
    "cookingforbeginners",
    "AskBaking",
    "AskCulinary"
]


def build_scanner_list():
    scanner_class_builder = {
        name: Scanner(
            sub_name=name,
            bot_name="CookingStatsBot",
            num_posts_to_scan=NUM_POSTS_TO_SCAN,
            interval_sec=SCANNER_INTERVAL_SEC
        ) for name in subreddit_list
    }

    for sub in subreddit_list:
        scanner_list.append(scanner_class_builder[sub])


def get_scanner_list() -> List[Scanner]:
    return scanner_list


def first_pass_completed() -> bool:
    for scanner in scanner_list:
        if not scanner.first_pass_done:
            return False

    return True


def get_cumulative_avg_runtime() -> int:
    cumulative_avg_runtime = 0

    for scanner in scanner_list:
        if scanner.first_pass_done:
            avg_runtime = scanner.get_avg_runtime_seconds()
            cumulative_avg_runtime += avg_runtime

    cumulative_avg_runtime_list.append(cumulative_avg_runtime)
    return round(cumulative_avg_runtime, 2)
