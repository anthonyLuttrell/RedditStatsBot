import datetime
import json
import math
import os
import praw
import sys
import time
from praw.exceptions import RedditAPIException
from prawcore import OAuthException
from args import get_args


def sys_exit():
    try:
        sys.exit(130)
    except SystemExit:
        os.system(exit(130))


class Scanner:
    time_slice = 1
    previous_day = get_args().day

    def __init__(self, sub_name: str, bot_name: str, num_posts_to_scan: int, sleep_seconds: int):
        self.sub_name = sub_name
        self.num_posts_to_scan = num_posts_to_scan
        self.sleep_seconds = sleep_seconds
        self.bot_name = bot_name
        self.sub_instance = self.get_subreddit_instance()
        self.is_mod = self.check_mod_invite()

    def log_in(self):
        return praw.Reddit(self.bot_name, user_agent="r/Cooking Stats Bot by u/96dpi")

    def get_subreddit_instance(self):
        # FIXME this is wrong, we are doing this every time we create a new Scanner object, we should only do it once
        try:
            print("Logged in as:", str(self.log_in().user.me()))
            return self.log_in().subreddit(self.sub_name)
        except OAuthException:
            print("Unable to log in! Verify the credentials in the praw.ini file. Terminating program.")
            sys_exit()

    def check_mod_invite(self) -> bool:
        try:
            self.sub_instance.mod.accept_invite()
            print("Mod invite accepted from r/" + self.sub_name + ", starting main program...")
            return True
        except RedditAPIException:
            print("No pending mod invites from r/" + self.sub_name +
                  ". Assuming the account u/" + self.bot_name +
                  " is already a mod with flair and wiki permissions, starting main program...")

    def get_time_slice(self):
        return self.time_slice

    def set_time_slice(self, new_time_slice):
        self.time_slice = new_time_slice

