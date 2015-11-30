# Self-Destruct Bot

A reddit bot that runs on your moderator account that removes posts after a set amount of time, though you need to implement the conditionals yourself. I left my working example, though it's rather ugly.

# Examples

_you'll know where this goes when you look at selfdestruct.py_

    expires_at_next_hour = ['http://www.neopets.com/freebies/tarlastoolbar.phtml', 'http://www.neopets.com/medieval/turmaculus.phtml']
    while True:
        for submission in subreddits.get_new(limit=25):
            # remove post at the beginning of the next hour
            if (submission.url in expires_at_next_hour):
                expires = next_hour(submission.created_utc)
                # expires = hours_later(submission.created_utc, 3) # alternatively, 3 hours after the post was made
                add_to_remove_list(submission, expires)
        check_temp() # where the magic happens
        time.sleep(60) # sleep for a minute. This is going forever, so it's a good idea.
