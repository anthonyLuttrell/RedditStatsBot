import Scanner

user_list = []


def set_user_flair(scanner: Scanner, list_of_users: list, flair_template_id: str, delete_first: bool):
    """Provides a method to manually delete and set user flair, if needed.

    Add each reddit username to `user_list` list, provide the function a Scanner
    object and a flair template ID, and it will delete and set user flair.

    Note: These operations take several seconds to complete, depending on the
    size of the subreddit.

    Args:
        scanner:
          A Scanner object that holds the reddit instance.
        list_of_users:
          A list of reddit usernames.
        flair_template_id:
          The flair template ID that you wish to apply.
        delete_first:
          True if you want to delete all user flair across the entire sub first.

    Returns:
        None
    """

    if delete_first:
        # this deletes the flair for all users of a subreddit!
        scanner.sub_instance.flair.delete_all()

    for user in list_of_users:
        scanner.sub_instance.flair.set(
            user,
            flair_template_id=flair_template_id
        )
