import os, praw, sqlite3, time, urllib2
from datetime import datetime, date, timedelta
import Config

# sqlite
conn = sqlite3.connect(Config.database_location)
c = conn.cursor()

r = praw.Reddit(user_agent='Post Self-Destruct (Auto-Remove) by /u/diceroll123')
print "Self-Destruct bot Logging in..."
r.login(Config.reddit_username, Config.reddit_password, disable_warning=True)
subreddits = r.get_subreddit(Config.subreddits)

def next_hour(timestamp): # returns timestamp of the nearest next hour
    original = datetime.fromtimestamp(int(timestamp))
    nearest_hour = original + timedelta(hours=1) - timedelta(minutes=original.minute, seconds=original.second, microseconds=original.microsecond)
    return int(time.mktime(nearest_hour.timetuple()))

def hours_later(timestamp, hours): # returns timestamp X hours after the post was made
    original = datetime.fromtimestamp(int(timestamp))
    hours_later = original + timedelta(hours=hours)
    return int(time.mktime(hours_later.timetuple()))

##### main functions

def check_temp():
    c.execute('SELECT * from temp')
    for (permalink, expires) in c.fetchall():
        if datetime.now() >= datetime.fromtimestamp(expires):
            submission = r.get_submission(permalink)
            try:
                print "Removing thread '%s' posted by /u/%s" % (submission.title, submission.author)
                submission.remove()

                c.execute("DELETE FROM temp WHERE link=?", (permalink,))
                conn.commit()
            except Exception, e:
                # if any errors occur while attempting to remove the thread (HTTP or otherwise), try again next loop.
                pass

def add_to_remove_list(submission, expires):
    if c.execute("SELECT link FROM temp WHERE link=?", (submission.permalink,)).fetchone() == None:
        c.execute('INSERT INTO temp(link, expires) VALUES (?, ?)', (submission.permalink, expires,))
        print "Added '%s' to temp" % submission.title

        conn.commit()

# debugging function(s) below
def clear_temp_table():
    c.execute("DELETE FROM temp")
    conn.commit()

##### main code

expires_at_next_hour = ['http://www.neopets.com/freebies/tarlastoolbar.phtml', 'http://www.neopets.com/medieval/turmaculus.phtml']
titles = ["tarla", "turmac"]

# clear_temp_table()
while True:
    try:
        for submission in subreddits.get_new(limit=25):
            # checks and balances
            if (submission.url in expires_at_next_hour or any(url in submission.selftext for url in expires_at_next_hour)) and any(name in submission.title.lower() for name in titles):
                expires = next_hour(submission.created_utc)
                add_to_remove_list(submission, expires)

        check_temp()
    except urllib2.HTTPError, e:
        if e.code in [429, 500, 502, 503, 504]:
            print "reddit is down, error %s!" % e.code # no biggie, just wait until next loop
            pass
        else:
            print "reddit broke"
            raise
    except Exception, e:
        print "Something, but still possibly reddit broke."
        raise
        
    time.sleep(60)
