import os
import praw
import sys
from praw.exceptions import RedditAPIException
from prawcore import OAuthException
from args import get_args


def sys_exit():
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))


class Scanner:
    previous_day = get_args().day

    def __init__(self, sub_name: str, bot_name: str, num_posts_to_scan: int, interval_sec: int):
        self.sub_name = sub_name
        self.num_posts_to_scan = num_posts_to_scan
        self.interval_seconds = interval_sec
        self.bot_name = bot_name
        self.sub_instance = self.get_subreddit_instance()
        self.is_mod = self.check_mod_invite()
        self.individual_avg_runtime_seconds = []
        self.first_pass_done = False

    def log_in(self):
        return praw.Reddit(self.bot_name, user_agent="r/Cooking Stats Bot by u/96dpi")

    def get_subreddit_instance(self):
        try:
            return self.log_in().subreddit(self.sub_name)
        except OAuthException:
            print("Unable to log in! Verify the credentials in the praw.ini file and try again. Terminating program.")
            sys_exit()

    def check_mod_invite(self) -> bool:
        try:
            self.sub_instance.mod.accept_invite()
            print("Mod invite accepted from r/" + self.sub_name)
            return True
        except RedditAPIException:
            print("No pending mod invites from r/" + self.sub_name)
            return False

    def append_avg_runtime_seconds(self, seconds: float):
        self.individual_avg_runtime_seconds.append(seconds)

    def get_avg_runtime_seconds(self) -> float:
        return 0 if len(self.individual_avg_runtime_seconds) == 0 \
            else sum(self.individual_avg_runtime_seconds) / len(self.individual_avg_runtime_seconds)
