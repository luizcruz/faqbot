#!/usr/bin/env python

import ConfigParser,csv,os,tweepy,random
from optparse import OptionParser
from time import gmtime, strftime

CONFIG_FILE = 'config.cfg'
LOG_FILE = 'log.txt'
API = ''

#Load Config File
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)

# Load Variables
csv_file_path = config.get('Import','csv_file_path')
csv_delimiter = config.get('Import','csv_delimiter')
aiml_file_dest = config.get('System','aiml_file_path')

def import_from_csv():

        # Import Routine
        csv_file = csv.reader(open(csv_file_path,'rb'),delimiter=csv_delimiter)
        aiml_file = open(aiml_file_dest,'w')
        aiml_file.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n\n<aiml>\n')
        for row in csv_file:
                if len(row[2]) <= 120:
                        what = row[1].strip()
                        mean = row[2].strip()
                        line = "<category><pattern>%s</pattern><template>%s</template></category>\n" % (what.upper(), mean.capitalize())
                        aiml_file.write(line)
        aiml_file.write('</aiml>')

	#Check if file is generated
	now = strftime("%a, %d %b %Y %H:%M:%S", gmtime())
	if os.path.getsize(aiml_file_dest)!= 0:
		print "\n%s - FAQbot -  AIML file generated \n" % (now)

		
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
			# config = ConfigParser.RawConfigParser()
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
		#config = ConfigParser.RawConfigParser()
		#config.read(CONFIG_FILE)
    consumer_key = config.get('OAuth', 'consumer_key')
    consumer_secret = config.get('OAuth', 'consumer_secret')
    access_key = config.get('OAuth', 'access_key')
    access_secret = config.get('OAuth', 'access_secret')

    # Create a new Tweepy instance, and set it global
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    global API
    API = tweepy.API(auth)


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

	
# Check for new mentions and answer them
def answer_mentions():
		#config = ConfigParser.RawConfigParser()
		#config.read(CONFIG_FILE)

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


# Continuously check for new unanswered mentions, and reply them
def run_bot():
		load_api() 
		answer_mentions() #TO-DO: loop


# Main routine
def main():

	#Load Options
	parser = OptionParser(usage="Usage: %prog [options]",version="%prog 1.0")
	parser.add_option("-p", "--parse",action="store_true", dest="parse",help="Parse data from csv defined in config.cfg")
	parser.add_option("-c", "--config",action="store_true", dest="config",help="Configure twitter account")
	parser.add_option("-a", "--answer", action="store_true", dest="answer",help="Run answer bot")
		
	#Parse Options	
	(options, args) = parser.parse_args()
	
	if ((options.parse and options.config) or (options.parse and options.answer) or (options.answer and options.config)):
		parser.error("Incorrect number of arguments")
	elif options.parse:
		import_from_csv()
	elif options.config:
		config_account()
	elif options.answer:
		run_bot()
	else:
		parser.error("You must provide an argument")	
		
		
if __name__ == "__main__":
    main()


