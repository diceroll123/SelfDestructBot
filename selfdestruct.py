import praw
import time
import sqlite3
from datetime import datetime, date, timedelta
import Config

class SelfDestruct:
  def __init__(self):
    self.conn = sqlite3.connect(Config.database_location)
    self.c = self.conn.cursor()

  @staticmethod
  def next_hour(timestamp): # returns timestamp of the nearest next hour
    original = datetime.fromtimestamp(int(timestamp))
    nearest_hour = original + timedelta(hours=1) - timedelta(minutes=original.minute, seconds=original.second, microseconds=original.microsecond)
    return int(time.mktime(nearest_hour.timetuple()))

  @staticmethod
  def hours_later(timestamp, hours): # returns timestamp X hours after the post was made
    original = datetime.fromtimestamp(int(timestamp))
    hours_later = original + timedelta(hours=hours)
    return int(time.mktime(hours_later.timetuple()))

  ##### main functions

  def check_temp(self):
    self.c.execute('SELECT * from temp')
    for (permalink, expires) in self.c.fetchall():
      if datetime.now() >= datetime.fromtimestamp(expires):
        submission = r.submission(id=permalink)
        try:
          print(f'Removing thread \'{submission.title}\' posted by /u/{submission.author}')
          submission.mod.remove()

          self.c.execute('DELETE FROM temp WHERE link=?', (permalink,))
          self.conn.commit()
        except Exception as e:
          print(e)
          # if any errors occur while attempting to remove the thread (HTTP or otherwise), try again next loop.
          pass

  def add_to_remove_list(self, submission, expires):
    if self.c.execute('SELECT link FROM temp WHERE link=?', (submission.id,)).fetchone() == None:
      self.c.execute('INSERT INTO temp(link, expires) VALUES (?, ?)', (submission.id, expires,))
      print(f'Added \'{submission.title}\' to temp')
      self.conn.commit()

  # debugging function(s) below
  def clear_temp_table(self):
    self.c.execute('DELETE FROM temp')
    self.conn.commit()

r = praw.Reddit('neopetsbot', user_agent='Automatically removes "expired" posts from /r/neopets. Maintained by /u/diceroll123.')

selfdestruct = SelfDestruct()
# selfdestruct.clear_temp_table()
expires_at_next_hour = ['http://www.neopets.com/freebies/tarlastoolbar.phtml', 'http://www.neopets.com/medieval/turmaculus.phtml']
titles = ['tarla', 'turmac', 'turmy']
buried_treasure = 'http://www.neopets.com/pirates/buriedtreasure/buriedtreasure.phtml?'

print('Logged in and awaiting subreddit stream.')

sub_stream = r.subreddit('neopets').stream.submissions(pause_after=3)

while True:
  try:
    for submission in sub_stream:
      if submission is None:
        break # checking time!

      if submission.approved_by == None: # meaning...it won't possibly be removed. (again)
        if (submission.url in expires_at_next_hour or any(url in submission.selftext for url in expires_at_next_hour)) and any(name in submission.title.lower() for name in titles):
          expires = SelfDestruct.next_hour(submission.created_utc)
          selfdestruct.add_to_remove_list(submission, expires)

        if (buried_treasure in submission.url or buried_treasure in submission.selftext):
          expires = SelfDestruct.hours_later(submission.created_utc, 1)
          selfdestruct.add_to_remove_list(submission, expires)
    selfdestruct.check_temp()
  except Exception as e:
    print(e)
    pass
