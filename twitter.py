#! /usr/bin/env python

import tweepy
import ConfigParser
import random

CONFIG_FILE = 'config.cfg'
LOG_FILE = 'log.txt'
API = ''

# TO-DO
# Bot implementation will go here.
# Currently, returns a random number (Twitter doesn't
# accept the same message twice).
def answer_bot(question):
    return 'resposta ' + str(random.randint(1,1000))


# Given a certain tweet, update the log file. Used for
# tracking the answering behavior of the bot.
# entry_type: Q (question) or A (answer)
def update_log(entry_type, tweet):
    entry_time = str(tweet.created_at)
    entry_user = str(tweet.user.id)
    entry_tweet_id = str(tweet.id)
    entry_text = tweet.text
    entry = entry_type + '\t' + entry_time + '\t' + entry_user + '\t' + entry_tweet_id + '\t' + entry_text + '\n'
    log_stream = open(LOG_FILE, 'a')
    log_stream.write(entry)
    log_stream.close()


#OAuth management
def config_account():
    # OAuth configuration
    print('Please, insert your Twitter App Data:')
    consumer_key = raw_input('Consumer Key: ').strip()
    consumer_secret = raw_input('Consumer Secret: ').strip()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    print('Generate PIN: ' + auth.get_authorization_url())
    pin = raw_input('PIN: ').strip()

    auth.get_access_token(pin)
    access_key = auth.access_token.key
    access_secret = auth.access_token.secret

    # Save the keys on the configuration file,
    # using Python native module ConfigParser
    config = ConfigParser.RawConfigParser()
    config.add_section('OAuth')    
    config.set('OAuth', 'consumer_key', consumer_key)
    config.set('OAuth', 'consumer_secret', consumer_secret)
    config.set('OAuth', 'access_key', access_key)
    config.set('OAuth', 'access_secret', access_secret)
    with open(CONFIG_FILE, 'wb') as cfgfile:
        config.write(cfgfile)

    print('OAuth data stored.')


# Generate a global instance of Tweepy
def load_api():
    # Load OAauth data, through ConfigParser module
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    consumer_key = config.get('OAuth', 'consumer_key')
    consumer_secret = config.get('OAuth', 'consumer_secret')
    access_key = config.get('OAuth', 'access_key')
    access_secret = config.get('OAuth', 'access_secret')

    # Create a new Tweepy instance, and set it global
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    global API
    API = tweepy.API(auth)


# Check for new mentions and answer them
def answer_mentions():
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)

    # Read last reply ID
    try:
        last_reply = config.getint('Replies', 'last_reply')

    # If there's no last reply ID stored, set it as 1 (first
    # possible tweet ID)
    except ConfigParser.NoSectionError:
        last_reply = 1
        config.add_section('Replies')
        config.set('Replies', 'last_reply',  last_reply)
        with open(CONFIG_FILE, 'wb') as cfgfile:
            config.write(cfgfile)    

    # Get the list of all non answered mentions so far, call 
    # the bot to answer them, tweet the results and update
    # the log 
    non_replieds = API.mentions(last_reply)
    non_replieds.reverse()
    if (non_replieds):
        print('There\'s %i mentions to be answered' % len(non_replieds))
        answer_count = 0;
        for message in non_replieds:
            update_log('Q', message)
            username = message.user.screen_name
            answer_content = answer_bot(message.text)
            reply_text = '@' + username + ' ' + answer_content
            reply_tweet = API.update_status(reply_text, message.id)
            update_log('A', reply_tweet)
        answer_count += 1

        # Update the last answered tweet ID
        config.set('Replies', 'last_reply', message.id)
        with open(CONFIG_FILE, 'wb') as cfgfile:
            config.write(cfgfile)
        print('Answered tweet %i/%i' % (answer_count, len(non_replieds)))

    else:
        print('There\'s no new mentions to be answered')


def main():
    load_api()
    answer_mentions()

    
if __name__ == '__main__': main()
