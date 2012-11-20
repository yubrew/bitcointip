﻿# -*- coding: utf-8 -*-
#from decimal import Decimal

import sys

import subprocess

#python reddit api wrapper
import praw

#bitcoindwrapper and custom methods
#txid = bitcoind.transact(fromthing, tothing, amount, txfee)
import bitcoind

#jsonrpc
from jsonrpc import ServiceProxy

#timestamp = round(time.time())
import time

#mysql database stuff
import pymysql

#datastring = urllib.request.urlopen(url).read()
import urllib

#jsonarray = json.loads(jsonstring)
#jsonstring = json.dumps(jsonarray)
import json

#regex stuff
import re

import string

import random


#todo correct type handling when retrieving from table.
######################################################################
#FUNCTIONS
######################################################################
    
#function for updating the timestamp of the most recent thing done
def set_last_time(thingtype, value):

    #check if user has been active at all.  If so, update, if not insert.
    entryexists = False
    
    sql = "SELECT * FROM TEST_TABLE_RECENT WHERE type='%s'" % (thingtype)
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        entryexists = True
    
    if (entryexists):
        #update username's lastactive time
        sql = "UPDATE TEST_TABLE_RECENT SET timestamp='%s' WHERE type='%s'" % (str(value), thingtype)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        print("Updated to MYSQL %s : %s" % (thingtype, str(value)))
    else:
        #insert username's lastactive time
        sql = "INSERT INTO TEST_TABLE_RECENT (type, timestamp) VALUES ('%s', '%s')" % (thingtype, str(value))
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        print("Inserted to MYSQL %s : %s" % (thingtype, str(value)))

def get_last_time(thingtype):
    #return a timestamp
    value = 0
    sql = "SELECT * FROM TEST_TABLE_RECENT WHERE type='%s'" % (thingtype)
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        value = row[1]
    print ("Retrieved from MYSQL %s : %s" % (thingtype, str(value)))

    try:
        value = int(value)
        return value
    except ValueError:
        try:
            value = json.loads(value)
            return value
        except Exception:
            return value
    
    
#manage allowed subreddits by those subscribed to by user bitcointip
def refresh_allowed_subreddits():
    global _lastallowedsubredditsfetched
    global _lastallowedsubredditsfetchedtime
    _lastallowedsubredditsfetched = []
    getreddits = _reddit.user.my_reddits()
    for subreddit in getreddits:
        _lastallowedsubredditsfetched.append(subreddit.display_name.lower())
    print ("Retrieved from REDDIT allowed subreddits:", _lastallowedsubredditsfetched)
    _lastallowedsubredditsfetchedtime = round(time.time())
    set_last_time("lastallowedsubredditsfetchedtime",_lastallowedsubredditsfetchedtime)
    set_last_time("lastallowedsubredditsfetched",json.dumps(_lastallowedsubredditsfetched))

        
        
#manage friends by those that have flair on the bitcointip subreddit
def refresh_friends():
    global _lastfriendsofbitcointipfetched
    global _lastfriendsofbitcointipfetchedtime
    _lastfriendsofbitcointipfetched = []
    bitcointipsubreddit = _reddit.get_subreddit("bitcointip")
    bitcointipfriends = bitcointipsubreddit.flair_list()
    for x in bitcointipfriends:
        if (x['flair_css_class']=="bitcoin"):
            _lastfriendsofbitcointipfetched.append(x['user'].lower())
    print ("Retrieved from REDDIT friends of bitcointip:", _lastfriendsofbitcointipfetched)
    _lastfriendsofbitcointipfetchedtime = round(time.time())
    set_last_time("lastfriendsofbitcointipfetchedtime", _lastfriendsofbitcointipfetchedtime)
    set_last_time("lastfriendsofbitcointipfetched", json.dumps(_lastfriendsofbitcointipfetched))


#refresh user flair on the bitcointip subreddit
def refresh_user_flair():
    
    sql = "SELECT * FROM TEST_TABLE_USERS WHERE giftamount!=0"
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()

    bitcointipsubreddit = _reddit.get_subreddit("bitcointip")
    for row in results:
        username = row[1]
        giftamount = float(row[5])
                    
        #based on newgiftamount, set flair and make friend if applicable
        if (giftamount>=2):
            #bitcoin level
            _reddit.get_redditor(transaction_from).friend()
            bitcointipsubreddit.set_flair(username, "Friend of Bitcointip", "bitcoin")
        elif (giftamount>=1):
            #gold level
            bitcointipsubreddit.set_flair(username, "Friend of Bitcointip", "gold")
        elif (giftamount>=0.5):
            #silver level
            bitcointipsubreddit.set_flair(username, "Friend of Bitcointip", "silver")
        elif (giftamount>=0.25):
            #bronze level
            bitcointipsubreddit.set_flair(username, "Friend of Bitcointip", "bronze")
            
    refresh_friends()

#manage banned users by banned from bitcointip subreddit
def refresh_banned_users():
    global _lastbannedusersfetched
    global _lastbannedusersfetchedtime
    _lastbannedusersfetched = []
    bitcointipsubreddit = _reddit.get_subreddit("bitcointip")
    bitcointipbanned = bitcointipsubreddit.get_banned()
    for x in bitcointipbanned:
        _lastbannedusersfetched.append(x.name.lower())
    print ("Retrieved from REDDIT banned users:", _lastbannedusersfetched)
    _lastbannedusersfetchedtime = round(time.time())
    set_last_time("lastbannedusersfetchedtime", _lastbannedusersfetchedtime)
    set_last_time("lastbannedusersfetched", json.dumps(_lastbannedusersfetched))

# GET THE EXCHANGE RATE FROM bitcoincharts.com
#USD,AUD,CAD,EUR,JPY,GBP
def refresh_exchange_rate():

    print ("Checking Exchange Rate...")

    global _lastexchangeratefetched
    global _lastexchangeratefetchedtime
    
    exchangecode = "mtgox"
    ratetype = "bid" #avg sometimes returns null

    #if exchangeratetime is less than updatetime hours ago, do nothing
    if ( ((round(time.time()))<(_lastexchangeratefetchedtime + _intervalupdateexchangerate)) ):
        return ""

    #else if the timestamp is over updatetime hours old, update the exchangerates
    else:
        url = "http://bitcoincharts.com/t/markets.json"
        file = urllib.request.urlopen(url)
        encoding = file.headers.get_content_charset()
        content =file.readall().decode(encoding)
        jsondata = json.loads(content)

        for row in jsondata:
            for symbol in _lastexchangeratefetched.keys():
                if (row['symbol'] == (exchangecode+symbol)):
                    _lastexchangeratefetched[symbol] = row[ratetype]
                    _lastexchangeratefetched[symbol] = round(_lastexchangeratefetched[symbol],2)
                    print ("Exchangerate '" + symbol + "' updated to " + str(_lastexchangeratefetched[symbol]))
        _lastexchangeratefetchedtime = round(time.time())
        set_last_time("lastexchangeratefetchedtime", _lastexchangeratefetchedtime)
        set_last_time("lastexchangeratefetched", json.dumps(_lastexchangeratefetched))


#addUser    
#add a user to the service and set them up with an address and account. returns "error" if unsuccessful.
def add_user(username):

    #check to see if user already exists.
    useralreadyexists = False
    sql = "SELECT * FROM TEST_TABLE_USERS WHERE username='%s'" % (username)
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        useralreadyexists = True

    if (not useralreadyexists):
        #create a deposit address for them
        newuseraddress = bitcoind.getnewaddress(username)
        if (newuseraddress == "error"):
            return "error"
            print ("Error getting new user address for new user", username)
        else:
            #add them to TABLE_USERS
            sql = "INSERT INTO TEST_TABLE_USERS (user_id, username, address, balance, datejoined) VALUES ('%s', '%s', '%s', '%.8f', '%f')" % (None, username, newuseraddress, 0.00000000, round(time.time()))
            _mysqlcursor.execute(sql)
            _mysqlcon.commit()
            print ("User (%s) added with address (%s)" % (username, newuseraddress))


#getUserBalance
#Get the current balance of a user. returns "error" if unsuccessful
def get_user_balance(username):

    #if not user, add user
    add_user(username)
    
    userbalance = bitcoind.getbalance(username)
    
    if (userbalance != "error"):
        return (float(userbalance))
    else: 
        if (add_user(username) == "error"):
            return "error"  
        else:
            return get_user_balance(username)

#getUserAddress
#Get the current address of a user. returns "error" if unsuccessful
def get_user_address(username):

    #if not user, add user
    add_user(username)

    useraddress = bitcoind.getaddressesbyaccount(username)[0]

    if (useraddress != "error"):
        return useraddress
    else: 
        if (add_user(username) == "error"):
            return "error"  
        else:
            return get_user_address(username)




#getUserGiftamount
#getUserGiftamount(username) get how much the user has donated to /u/bitcointip
def get_user_gift_amount(username):

    #if not user, add user
    add_user(username)

    sql = "SELECT * FROM TEST_TABLE_USERS WHERE username='%s'" % (username)

    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        giftamount = row[5]
        return float(giftamount)

    #if nothing was returned, the user doesn't exist yet. Add them. and try again.
    if (add_user(username) == "error"):
        return "error"
    else:
        return get_user_gift_amount(username)



#hasUserRedeemedKarma
#checks to see if a user has gotten bitcoins from the reddit bitcoin faucet yet.
def has_user_redeemed_karma(username):

    #if not user, add user
    add_user(username)

    alreadyredeemed = False
    sql = "SELECT * FROM TEST_TABLE_FAUCET_PAYOUTS WHERE username='%s'" % (username)
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        alreadyredeemed = True
        
    if (alreadyredeemed):
        print ("user has redeemed karma already.")
        return True
    else:
        print ("user has not redeemed karma yet.")
        return False


#doesTransactionExist
#double checks whether or not a transaction has already been done.
def does_transaction_exist(sender, receiver, timestamp):

    sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE sender_username='%s' AND receiver_username='%s' AND timestamp='%f'" % (sender, receiver, timestamp)
    _mysqlcursor.execute(sql)
    results = _mysqlcursor.fetchall()
    for row in results:
        #transaction already processed
        return True
    
    #transaction doesn't exist.
    return False

    
#create footer for the end of all PMs
def get_footer(username):
    footer = "\n\n---\n\n|||\n|:|:|\n| Account Owner: | **%s** |\n| Deposit Address: | **%s** |\n| Address Balance: | **&#3647;%.8f BTC** *(~$%.2f USD)* \n|\n\n[About Bitcointip](http://www.reddit.com/r/bitcointip) (BETA) **(TEST VERSION, DO NOT DEPOSIT!!!)**" % (username, get_user_address(username), get_user_balance(username), round(get_user_balance(username)*_lastexchangeratefetched['USD'],2))
    return footer
    
    
    
#doTransaction
#do the transaction
def do_transaction(transaction_from, transaction_to, transaction_amount, tip_type, tip_id, tip_subreddit, tip_timestamp):

    #returns success message or failure reason

    #update lastactive for the sender because they are using tips
    set_last_time("LASTACTIVE_"+transaction_from, round(time.time()))
    
    print ("doing transaction")
    
    #Search for transaction in transaction list to prevent double processing!
    if (does_transaction_exist(transaction_from, transaction_to, tip_timestamp)):
        print ("Transaction does already exist.")
        return ("error")

    #if the transaction is to a reddit user, make sure they are set up with an account.
    if (bitcoind.validateaddress(transaction_to)['isvalid'] == False):
        add_user(transaction_to)

    #SEND tips to bitcointip to cold storage.  Don't have the private key on the server.
    bitcointipcoldstorage = "1K3ZXpqUkntLR4uVUSW8FK3aRrFnSjeGEm"
    if (transaction_to.lower()=="bitcointip"):
        transaction_to = bitcointipcoldstorage #replace with cold storage public address.

    #submit the transaction to the wallet.
    txid = bitcoind.transact(transaction_from, transaction_to, transaction_amount, _txfee)

    if (transaction_to == bitcointipcoldstorage):
        transaction_to = "bitcointip"
    
    print ("txid: ", txid)
    
    #based on the statusmessage, set the status and process.
    if (txid != "error"):
        status = "pending"
        
        if (bitcoind.validateaddress(transaction_to)['isvalid']):
            #we are sending to an address (not reversable)
            status = "completed"
    
        
        #do a transaction from sender to reciever for amount. put into TABLE_TRANSACTIONS
        sql = "INSERT INTO TEST_TABLE_TRANSACTIONS (transaction_id, sender_username, sender_address, receiver_username, receiver_address, amount_BTC, amount_USD, type, url, subreddit, timestamp, verify, statusmessage, status) VALUES ('%s', '%s', '%s', '%s', '%s', '%.8f', '%.2f', '%s', '%s', '%s', '%f', '%s', '%s', '%s')" % (txid, transaction_from, transaction_from, transaction_to, transaction_to, transaction_amount, round(transaction_amount*_lastexchangeratefetched['USD'],2), tip_type, tip_id, tip_subreddit, tip_timestamp, "null", "null", status)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
    
    
        #if tip is to bitcointip, add tip to giftamount for sender.
        if ( transaction_to.lower() == "bitcointip" ):
            oldgiftamount = get_user_gift_amount(transaction_from)
            newgiftamount = oldgiftamount + transaction_amount
            sql = "UPDATE TEST_TABLE_USERS SET giftamount='%.8f' WHERE username='%s'" % (newgiftamount, transaction_from)
            _mysqlcursor.execute(sql)
            _mysqlcon.commit()
            
            bitcointipsubreddit = _reddit.get_subreddit("bitcointip")
            #based on newgiftamount, set flair and make friend if applicable
            if (newgiftamount>=2):
                #bitcoin level
                _reddit.get_redditor(transaction_from).friend()
                bitcointipsubreddit.set_flair(transaction_from, "Friend of Bitcointip", "bitcoin")
                #refresh friends list to reflect new addition
                refresh_friends()
            elif (newgiftamount>=1):
                #gold level
                bitcointipsubreddit.set_flair(transaction_from, "Friend of Bitcointip", "gold")
            elif (newgiftamount>=0.5):
                #silver level
                bitcointipsubreddit.set_flair(transaction_from, "Friend of Bitcointip", "silver")
            elif (newgiftamount>=0.25):
                #bronze level
                bitcointipsubreddit.set_flair(transaction_from, "Friend of Bitcointip", "bronze")
                
            #make all transactions to 'bitcointip' completed
            sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE receiver_username='bitcointip'" 
            _mysqlcursor.execute(sql)
            _mysqlcon.commit()
        
        print ("Transaction Successful:", transaction_from, ">>>>", transaction_amount, ">>>>", transaction_to)
        return txid
        
    else:
        #(txid == "error") the transaction didn't go through right. and is canceled
        
        status = "cancelled"
        
        #even though canceled, enter into transaction list but as cancelled
        sql = "INSERT INTO TEST_TABLE_TRANSACTIONS (transaction_id, sender_username, sender_address, receiver_username, receiver_address, amount_BTC, amount_USD, type, url, subreddit, timestamp, verify, statusmessage, status) VALUES ('%s', '%s', '%s', '%s', '%s', '%.8f', '%.2f', '%s', '%s', '%s', '%f', '%s', '%s', '%s')" % (txid, transaction_from, transaction_from, transaction_to, transaction_to, transaction_amount, round(transaction_amount*_lastexchangeratefetched['USD'],2), tip_type, tip_id, tip_subreddit, tip_timestamp, "null", "null", status)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        print ("Transaction Cancelled:", transaction_from, ">>>>", transaction_amount, ">>>>", transaction_to)
        return "error"
    

    
    

#update_transactions
#updates pending transactions to completed or reversed depending on receiver activity
def update_transactions():
    print ("Updating Pending Transactions...")
    
    global _lastpendingupdatedtime
    global _lastpendingnotifiedtime
    
    ##get TRANSACTIONS_UPDATED timestamp from TEST_TABLE_RECENT
    _lastpendingupdatedtime = get_last_time("lastpendingupdatedtime")
    
    
    print ("Last Pending Transactions Update Time:", _lastpendingupdatedtime)
        
        
    ##do this once every day
    ##if (transactiontime + 21days)< receiverlastactive, process the reversal of the transaction to the senders new address, and set transactionstatus=reversed.

    if (round(time.time()) >= (_lastpendingupdatedtime + (_intervalpendingupdate))):
        ##if the transactions haven't been updated in 1 day, do the update.
        print ("Updating Pending Transactions")
        
        #go through each pending transaction and evaluate it.
        sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE status='pending'"
        _mysqlcursor.execute(sql)
        results = _mysqlcursor.fetchall()
        for row in results:
            transactionid = row[0]
            receiver = row[3]
            sender = row[1]
            timestamp = float(row[10])
            transactionamount = float(row[5])
            

            receiverlastactive = get_last_time("LASTACTIVE_"+receiver)
            if (receiverlastactive > timestamp):
                #mark transaction as completed because user has been active after transaction
                sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE transaction_id='%s" % (transactionid)
                _mysqlcursor.execute(sql)
                _mysqlcon.commit()
            elif ( round(time.time()) > (timestamp + _intervalpendingcancel) ):
                #transaction is older than 21 days and pending...try to reverse
                ##check to make sure the reciever has enough
                receiverbalance = get_user_balance(receiver)
                if (receiverbalance >= (transactionamount)):
                    ##the receiver has enough, just move the coins from the receiveraddress back to the new senderaddress
                    reversalamount = transactionamount - _txfee
                    
                    reversalstatus = bitcoind.transact(receiver, sender, reversalamount, _txfee)
                    
                    ##mark the transaction as reversed in the table
                    if(reversalstatus != "error"):
                        sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='reversed' WHERE transaction_id='%s'" % (transactionid)
                        _mysqlcursor.execute(sql)
                        _mysqlcon.commit()
                        print ("Transaction reversed: ", transactionid)
                    else:
                        ##the user doesn't have enough to reverse the transaction, they must have spent it in another way.
                        sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE transaction_id='%s'" % (transactionid)
                        _mysqlcursor.execute(sql)
                        _mysqlcon.commit()
                        print ("Transaction completed (user already spent funds):", transactionid)
                else:
                    ## the receiver doesn't have enough.  They must have already spent it
                    ##mark as completed instead of reversed.
                    sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE transaction_id='%s'" % (transactionid)
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                    print ("Transaction completed (user already spent funds):", transactionid)
            

        
        
        #Get ready to send out weekly notifications to users who have pending transactions to them that they need to accept.
        ##get TRANSACTIONS_NOTIFIED timestamp from TEST_TABLE_RECENT
            _lastpendingnotifiedtime = get_last_time("lastpendingnotifiedtime")
            print ("Last Notify Time:", _lastpendingnotifiedtime)
        
        
    
        
        ##do notifications weekly, not daily.
        if ( round(time.time()) >=(_lastpendingnotifiedtime + _intervalpendingnotify) and False):
            print ("Going through each user to see if need to notify")
    
            ##go through each user and compile list of pending transactions to them.
            sql = "SELECT * FROM TEST_TABLE_USERS WHERE 1"
            _mysqlcursor.execute(sql)
            result = _mysqlcursor.fetchall()
            for row in result:
                username = row[1]
                havependingtransaction = False
                
                sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE receiver_username='%s' AND status='pending' ORDER BY timestamp ASC" % (username)
                _mysqlcursor.execute(sql)
                resultb = _mysqlcursor.fetchall()
                for row in resultb:
                    havependingtransaction = True
                    oldesttransaction = float(row[10])
            
                if (havependingtransaction):
                
                    print (username, " has a pending transaction")
                    message = "One or more of your received tips is pending.  If you do not take action, your account will be charged and the tip will be returned to the sender.  To finalize your ownership of the tip, send a message to bitcointip with ACCEPT in the message body.  To return it, send DECLINE.  The oldest pending tip(s) will be returned to the sender in ~%d days." % (round((oldesttransaction + (_intervalpendingcancel) - round(time.time()))/(60*60*24)))
                    
                    ##Add on a list of transactions since oldesttransaction
                    ##add first line of transaction table headers to the response.
                    transactionhistorymessage = "\n#**%s's Pending Transaction History***\n\nDate | Sender | Receiver | BTC | ~USD | Status |\n|:|:|:|:|:|:|\n" % (username)
                    k = 0

                    sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE (sender_username='%s' OR receiver_username='%s' ) AND timestamp>=%f ORDER BY timestamp DESC" % (username, username, oldesttransaction)
                    _mysqlcursor.execute(sql)
                    resultc = _mysqlcursor.fetchall()
                    for row in resultc:
                        if (k<10):
                            sender = row[1]
                            receiver_username = row[3]
                            receiver_address = row[4]
                            amount_BTC = float(row[5])
                            amount_USD = float(row[6])
                            status = row[13]
                            timestamp = float(row[10])
                            
                            ##if tip is sent directly to address with no username, display address.
                            if (receiver_username == ""):
                                receiver = receiver_address
                            else:
                                receiver = receiver_username
                                
                            date = time.strftime("%a %d-%b-%Y", time.gmtime())

                            ##add new transaction row to table being given to user
                            newrow = "| %s | %s | %s | %.8f | $%.2f | %s |\n" % (date, sender, receiver, amount_BTC, amount_USD, status)
                            transactionhistorymessage = transactionhistorymessage + newrow
                        else:
                            #k = 10
                            transactionhistorymessage = transactionhistorymessage + "**Transaction History Truncated.*\n\n"
                        k += 1
                    
                        
        
                    transactionhistorymessage = transactionhistorymessage + "**Only includes tips to or from your Reddit username.*\n\n"
        
                    message = message + transactionhistorymessage
                
                    #add footer
                    message = message + get_footer(username)
                
                    ##put message in to submit table
                    sql = "INSERT INTO TEST_TABLE_TOSUBMIT (type, replyto, subject, text, captchaid, captchasol, sent, timestamp) VALUES ('message', '%s', 'Bitcointip Pending Transaction(s) Notice', '%s', '', '', '0', '%f')" % (username, message, round(time.time()))
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                
                    print ("Notification of Pending transaction(s) prepared for", username)
                    
                _lastpendingnotifiedtime = round(time.time())
            set_last_time("lastpendingnotifiedtime", _lastpendingnotifiedtime)
            print ("TRANSACTIONS_INSERTED(NOTIFIED) to ", _lastpendingnotifiedtime)
                
            
        else:
        
            print ("Not time to make notifications yet.")
            
    
    
    
        _lastpendingupdatedtime = round(time.time())
        set_last_time("lastpendingupdatedtime", _lastpendingupdatedtime)
        print ("<br><br>TRANSACTIONS_UPDATED(UPDATED) to ", round(time.time()))
    
    else:
        print ("Not Updating Pending Transactions")
    

    
def eval_tip(thing):
    #evaluates a user tip, does the tip if valid, and then sends comment reply and messages if needed
    thing.body = thing.body.replace("&amp;","&")
    #Speed things up by doing these simple checks:
    #check body for bitcointip command keyword. if no result, return 0
    regex_keyword_string = "(\\+(bitcointip|bitcoin|tip|btctip|bittip|btc))"
    regex_keyword = re.compile(regex_keyword_string,re.IGNORECASE)
    tip_command_keyword = regex_keyword.search(thing.body)
    if (not tip_command_keyword):
        return 0
    #check author's balance.  if 0, return 0
    add_user(thing.author.name)
    if (get_user_balance(thing.author.name)<=0):
        return 0

    amount_value = 0
    amount_code = ""
    amount_symbol = ""
    transaction_amount = 0
    transaction_from = ""
    transaction_to = ""

    disallowed_usernames = ["flip", "all"]
    
    
    ##List the properties the tip could have
    transaction_from = thing.author.name
    tip_timestamp = round(thing.created_utc)
    tip_id = thing.name
    
    if (thing.subreddit is not None):
        tip_subreddit = thing.subreddit.display_name.lower()
    else:
        tip_subreddit = "none"
    try:    
        if (thing.dest=="bitcointip"):
            tip_type = "message"
    except:
        tip_type = "comment"
    
    #Now get the properties of the tip string
    ##isolate the tipping command
    regex_start_string = "(\\+(bitcointip|bitcoin|tip|btctip|bittip|btc))" #start tip 0
    regex_bitcoinaddress_string = regex_start_string+" (@?((1|3)[A-Za-z0-9]{25,35}))\\b" #bitcoin address
    regex_redditusername_string = regex_start_string+" (@?([A-Za-z0-9_-]{3,20}))\\b" #reddit username
    regex_currencysymbol_string = " ((\$)|&#36;|฿|&#3647;|&bitcoin;|¥|&#165;|&yen;|£|&#163;|&pound;|€|&#8364;|&euro;)"
    regex_currencyamount_string = "((\\d{1,3}(\\,\\d{3})*|(\\d+))(((\\.)(((\\d{3}\\,\\d{3}\\,\\d{1,2})|(\\d{3}\\,\\d{1,3}))|(\\d{1,8})))?))"
    regex_currencycode_string = "((BTC|XBC|bitcoin|mBTC|CBC|MBC|millibitcoin|millibit|cBTC|bitcent|centibit|centibitcoin|USD|dollar|american|AUD|australian|CAD|canadian|GBP|pound|EUR|euro|JPY|yen)(s)?)"
    regex_all_string = "(\\bALL\\b)" #all keyword
    regex_flip_string = "(\\bFLIP\\b)" #flip keyword
    regex_amount_string = "((\\b("+regex_currencysymbol_string+"? ?("+regex_currencyamount_string+") ?"+regex_currencycode_string+"?)\\b)|"+regex_all_string+"|"+regex_flip_string+")"
    regex_verify_string = "(\\b(NOVERIFY|VERIFY)\\b)" #noverify keyword
    regex_internet_string = "(\\+1 internet(s)?)" #internet keyword

    regex_tip_string = "((\\+(bitcointip|bitcoin|tip|btctip|bittip|btc)( ((@?1[A-Za-z0-9]{25,35})|((@)?([A-Za-z0-9_-]{3,20}))))?( ((((\$)|&#36;|฿|&#3647;|&bitcoin;|¥|&#165;|&yen;|£|&#163;|&pound;|€|&#8364;|&euro;)? ?((\\d{1,3}(\\,\\d{3})*|(\\d+))(((\\.)(((\\d{3}\\,\\d{3}\\,\\d{1,2})|(\\d{3}\\,\\d{1,3}))|(\\d{1,8})))?))( ?(BTC|XBC|bitcoin|mBTC|CBC|MBC|millibitcoin|millibit|cBTC|bitcent|centibit|centibitcoin|USD|dollar|american|AUD|australian|CAD|canadian|GBP|pound|EUR|euro|JPY|yen)(s)?)?)|ALL|FLIP))( (NOVERIFY|VERIFY))?)|(\\+1 internet(s)?))"

    regex_start = re.compile(regex_start_string,re.IGNORECASE)
    regex_bitcoinaddress = re.compile(regex_bitcoinaddress_string,re.IGNORECASE)
    regex_redditusername = re.compile(regex_redditusername_string,re.IGNORECASE)
    regex_amount = re.compile(regex_amount_string,re.IGNORECASE)
    regex_all = re.compile(regex_all_string,re.IGNORECASE)
    regex_flip = re.compile(regex_flip_string,re.IGNORECASE)
    regex_verify = re.compile(regex_verify_string,re.IGNORECASE)
    regex_internet = re.compile(regex_internet_string,re.IGNORECASE)
    regex_tip = re.compile(regex_tip_string,re.IGNORECASE)

    #isolate the tip_command from the text body
    tip_command = regex_tip.search(thing.body)
    if (tip_command):
        print (tip_command.groups())
        tip_command = tip_command.groups()[0]
        print ("command:",tip_command)
        
        tip_command_start = regex_start.search(tip_command)
        if (tip_command_start):
            #print (tip_command_start.groups())
            tip_command_start = tip_command_start.groups()[1]
            print ("command_start:",tip_command_start)
        else:
            tip_command_start = ""
            
        tip_command_bitcoinaddress = regex_bitcoinaddress.search(tip_command)
        if (tip_command_bitcoinaddress):
            #print (tip_command_bitcoinaddress.groups())
            tip_command_bitcoinaddress = tip_command_bitcoinaddress.groups()[3]
            print ("command_bitcoinaddress:",tip_command_bitcoinaddress)
        else:
            tip_command_bitcoinaddress = ""
            
        tip_command_redditusername = regex_redditusername.search(tip_command)
        if (tip_command_redditusername):
            #print (tip_command_redditusername.groups())
            tip_command_redditusername = tip_command_redditusername.groups()[3]
            if (tip_command_redditusername.lower() in disallowed_usernames):
                tip_command_redditusername = ""
            print ("command_redditusername:",tip_command_redditusername)
        else:
            tip_command_redditusername = ""
            
        tip_command_amount = regex_amount.search(tip_command)
        if (tip_command_amount):
            #print (tip_command_amount.groups())
            tip_command_amount = tip_command_amount.groups()[0]
            print ("command_amount:",tip_command_amount)
        else:
            tip_command_amount = ""
            
        tip_command_all = regex_all.search(tip_command)
        if (tip_command_all):
            #print (tip_command_all.groups())
            tip_command_all = tip_command_all.groups()[0]
            print ("command_all:",tip_command_all)
        else:
            tip_command_all = ""
            
        tip_command_flip = regex_flip.search(tip_command)
        if (tip_command_flip):
            #print (tip_command_flip.groups())
            tip_command_flip = tip_command_flip.groups()[0]
            print ("command_flip:",tip_command_flip)
        else:
            tip_command_flip = ""

        tip_command_verify = regex_verify.search(tip_command)
        if (tip_command_verify):
            print (tip_command_verify.groups())
            tip_command_verify = tip_command_verify.groups()[0]
            print ("command_verify:",tip_command_verify)
        else:
            tip_command_verify = ""
            
        tip_command_internet = regex_internet.search(tip_command)
        if (tip_command_internet):
            print (tip_command_internet.groups())
            tip_command_internet = tip_command_internet.groups()[0]
            print ("command_internet:",tip_command_internet)
        else:
            tip_command_internet = ""
        
    else:
        tip_command = ""
        print ("No tip found in", tip_type)
        return 0

    #no reason to give a cancel message yet.
    cancelmessage=""
    flipresult = -1
    
    #get transaction_to
    if (tip_command_redditusername):
        tip_command_redditusername = tip_command_redditusername.strip('@')
        tip_command_redditusername = tip_command_redditusername.strip(' ')
        transaction_to = tip_command_redditusername
    elif (tip_command_bitcoinaddress):
        tip_command_bitcoinaddress = tip_command_bitcoinaddress.strip('@')
        tip_command_bitcoinaddress = tip_command_bitcoinaddress.strip(' ')
        transaction_to = tip_command_bitcoinaddress
    elif (tip_type == "comment"):
        #recipient not specified, get author of parent comment todo
        print ("COMMENT PERMALINK:",thing.permalink)
        parentpermalink = thing.permalink.replace(thing.id, thing.parent_id[3:])
        print ("PARENT PERMALINK:", parentpermalink)
        
        
        commentlinkid = thing.link_id[3:]
        commentid = thing.id
        parentid = thing.parent_id[3:]
        authorid = thing.author.name


        
        #print ("SUBMISSIONID:", commentlinkid)
        #print ("COMMENTID:",commentid)
        #print ("PARENTID:",parentid)
        #print ("AUTHORID:",authorid)

        #print ("\n")

        if (commentlinkid==parentid):
            parentcomment = _reddit.get_submission(parentpermalink)
        else:
            parentcomment = _reddit.get_submission(parentpermalink).comments[0]
            

        #parentcommentlinkid = parentcomment.link_id[3:]
        #parentcommentid = parentcomment.id
        #parentparentid = parentcomment.parent_id[3:]
        parentauthorid = parentcomment.author.name

        #print ("PARRENTSUBMISSIONID:", parentcommentlinkid)
        #print ("PARENTCOMMENTID:",parentcommentid)
        #print ("PARENTPARENTID:",parentparentid)
        print ("PARENTAUTHORID:",parentauthorid)
            
        transaction_to = parentauthorid
        print ("TRANSACTION_TO:",transaction_to)
    elif (tip_type == "message"):
        #malformed tip
        #must include recipient
        #error
        print ("No recipient found in tip... not a tip.")
        cancelmessage = "You must include a recipient."

    
    #from amount get the currency and do a conversion if necesarry

    amount_symbol_list = ("&#3647;","&#36;","&#165;","&#163;","&#8364;")
    amount_code_list = ("XBC","CBC","MBC","UBC","SBC","USD","JPY","GBP","EUR","CAD","AUD")
    standardizing_symbol_dictionary = {
                                "฿":"&#3647;",
                                "¥":"&#165;",
                                "£":"&#163;",
                                "€":"&#8364;",
                                "$":"&#36;",
                                "&bitcoin;":"&#3647;",
                                "&yen;":"&#165;",
                                "&pound;":"&#163;",
                                "&euro;":"&#8364;"}
                                
    standardizing_code_dictionary =  {
                                "millibitcoin":"MBC",
                                "microbitcoin":"UBC",
                                "bitcoin":"XBC",
                                "bitcent":"CBC",
								"centibitcoin":"CBC",
								"centibit":"CBC",
                                "millibit":"MBC",
                                "microbit":"UBC",
                                "satoshi":"SBC",
                                "mbtc":"MBC",
                                "&#181;btc":"UBC",
                                "&micro;btc":"UBC",
                                "ubtc":"UBC",
                                "cbtc":"CBC",
                                "american":"USD",
                                "canadian":"CAD",
                                "australian":"AUD",
                                "usd":"USD",
                                "dollar":"USD",
                                "gbp":"GBP",
                                "pound":"GBP",
                                "aud":"AUD",
                                "cad":"CAD",
                                "euro":"EUR",
                                "eur":"EUR",
                                "jpy":"JPY",
                                "yen":"JPY",
                                "btc":"XBC",
                                "xbc":"XBC",
                                "sat":"SBC",
                                }

    symbol_code_dictionary = {"XBC":"&#3647;",
                              "CBC":"",
                              "MBC":"",
                              "UBC":"",
                              "SBC":"",
                              "JPY":"&#165;",
                              "GBP":"&#163;",
                              "EUR":"&#8364;",
                              "CAD":"&#36;",
                              "AUD":"&#36;",
                              "USD":"&#36;"}
    
    #get transaction_amount
    if (tip_command_amount or tip_command_internet):
        #standardize
        if (tip_command_amount):
            tip_command_amount = tip_command_amount.lower()
            tip_command_amount = tip_command_amount.replace(" ","")
            tip_command_amount = tip_command_amount.strip("s")

            #not needed thanks to the encoding.decoding handled before the function gets the text.
            for key in standardizing_symbol_dictionary:
                if (key in tip_command_amount):
                    tip_command_amount = tip_command_amount.replace(key, standardizing_symbol_dictionary[key])

            longestcode = 0
            for key in standardizing_code_dictionary:
                if (key in tip_command_amount):
                    if (longestcode<key.__len__()):
                        longestcode = key.__len__()
                        
            for key in standardizing_code_dictionary:
                if (key in tip_command_amount):
                    if (key.__len__() == longestcode):
                        tip_command_amount = tip_command_amount.replace(key, standardizing_code_dictionary[key])
                        break
                    
            print ("Sanitized amount command:", tip_command_amount)
        if (tip_command_amount!="all" and tip_command_amount!="flip" and (not tip_command_internet)):
            #reduce duplicates

            for key in amount_symbol_list:
                if (key in tip_command_amount):
                    amount_symbol=key

            if (tip_command_amount[-3:] in amount_code_list):
                amount_code = tip_command_amount[-3:]
            else:
                amount_code = ""

            if (bool(amount_code) and bool(amount_symbol)):
                if (symbol_code_dictionary[amount_code]!=amount_symbol):
                    print ("Code and symbol mismatch")
                    return 0

            if (bool(amount_code)==False and bool(amount_symbol)==False):
                print ("no symbol or code in tip. units????")
                return 0

            if (bool(amount_code)==False and bool(amount_symbol)==True):
                #make code from symbol
                if (amount_symbol=="&#36;"):
                    amount_code="USD"
                else:
                    for code in symbol_code_dictionary:
                        if (symbol_code_dictionary[code]==amount_symbol):
                            amount_code = code
                        
            if (bool(amount_code)==True and bool(amount_symbol)==False):
                #make symbol from code
                amount_symbol = symbol_code_dictionary[amount_code]
                
            
            amount_value = tip_command_amount

            for i in string.ascii_letters:
                #print (amount_value)
                amount_value = amount_value.replace(i,"")
            for symbol in amount_symbol_list:
                amount_value = amount_value.replace(symbol,"")
            amount_value = amount_value.replace(",","")
     
            try:
                amount_value = float(amount_value)
            except ValueError:
                print ("No amount was able to be found. Quitting.")
                #return 0

            print ("Value:",amount_value)
            print ("Symbol:",amount_symbol)
            print ("Code:",amount_code)
            #print (_lastexchangeratefetched)
            #print (_lastexchangeratefetched[amount_code])
            #convert amount_value and amount_code to a bitcoin amount
            transaction_amount = (amount_value/(_lastexchangeratefetched[amount_code]))
            transaction_amount = round(transaction_amount, 8)
            
        elif (tip_command_all):
                senderbalance = get_user_balance(transaction_from)
                transaction_amount = (senderbalance - _txfee)
                transaction_amount = round(transaction_amount, 8)
                amount_value=transaction_amount
                amount_symbol="&#3647;"
                amount_code="XBC"
                
        elif (tip_command_flip):
            if (get_user_balance(transaction_from)>=0.0105):
                if (get_user_gift_amount(transaction_from)>=0.25):
                    ##do a coin flip
                    flipresult = round(random.random())
                    if (flipresult==1):
                        transaction_amount = 0.01
                    else:
                        transaction_amount = 0
                else:
                    #error: not donated enough
                    cancelmessage = "You have not donated enough to use the flip command."
                    transaction_amount = 0
            else:
                #error: not enough balance
                cancelmessage = "You do not have a bitcent (and fee) to flip."
                transaction_amount = 0
            amount_value=transaction_amount
            amount_symbol="&#3647;"
            amount_code="XBC"
            
        elif (tip_command_internet):
            if (get_user_gift_amount(transaction_from)>=1):
                if ("s" in tip_command_internet.lower()):
                    transaction_amount = 0.02
                    if (get_user_balance(transaction_from)<0.0205):
                        cancelmessage = "You do not have 2 internets (&#3647;0.02) to give." #not sent to user
                else:
                    transaction_amount = 0.01
                    if (get_user_balance(transaction_from)<0.0105):
                        cancelmessage = "You do not have an internet (&#3647;0.01) to give." #not sent to user
            else:
                #error: not donated enough 
                cancelmessage = "You have not donated enough to use the +1 internet command." #not sent to user
                transaction_amount=0
                
            amount_value=transaction_amount
            amount_symbol="&#3647;"
            amount_code="XBC"
        
    ##check conditions to cancel the transaction and return error message
    if (transaction_amount<=0 and (not tip_command_flip) and cancelmessage==""):
        cancelmessage = "You cannot send an amount of 0 or less."
    elif (transaction_amount+_txfee > get_user_balance(transaction_from) and cancelmessage==""):
        cancelmessage = "You do not have enough in your account.  You have &#3647;%.8f BTC, but need &#3647;%.8f BTC (do not forget about the &#3647;%f BTC fee per transaction)." % (get_user_balance(transaction_from), transaction_amount+_txfee, _txfee)
    elif ( tip_type=="comment" and (tip_subreddit not in _lastallowedsubredditsfetched) and (get_user_gift_amount(transaction_from)<2) and cancelmessage==""):
        cancelmessage = "The %s subreddit is not currently supported for you." % (tip_subreddit)
    elif ((transaction_from.lower() in _lastbannedusersfetched) and transaction_from!="" and cancelmessage==""):
        cancelmessage="You are not allowed to send or receive money."
    elif ((transaction_to.lower() in _lastbannedusersfetched) and transaction_to!="" and cancelmessage==""):
        cancelmessage="The user %s is not allowed to send or receive money." % (transaction_to)
    elif (transaction_to == transaction_from and cancelmessage==""):
        cancelmessage="You cannot send any amount to yourself."
    elif (transaction_to == "" and cancelmessage==""):
        cancelmessage="You must specify a recipient username or bitcoin address."
        
    #todo, don't do tx if flipresult=0
    if (cancelmessage or (tip_command_flip and flipresult==0)):
        txid="error"
    else:
        if (tip_command_redditusername):
            add_user(transaction_from)
        txid = do_transaction(transaction_from, transaction_to, transaction_amount, tip_type, tip_id, tip_subreddit, tip_timestamp)
        if (txid == "error"):
            cancelmessage = "There was a problem with the transaction that probably was not your doing."
    
    #based on the variables, form messages.
    
    #form currency amount based on what user used
    #if user specified currency other than BTC, use BTC as main and theirs as alternate.  If user specified BTC, default to USD as alternate
    if (amount_code):
        if (amount_code[-2:]!="BC"):
            altcurrency_code = amount_code
        else:
            altcurrency_code = "USD"
    else:
        altcurrency_code = "USD"
        
    altcurrency_symbol = symbol_code_dictionary[altcurrency_code]
    altcurrency_amount = round(transaction_amount * (_lastexchangeratefetched[altcurrency_code]),2)

    #link to the transaction is hidden in the bitcoin symbol
    verifiedmessage = "[[**✔**](https://blockchain.info/tx/%s)] **Verified**:[ %s ---> **&#3647;%.8f BTC** *(%s%.2f %s)* ---> %s ](http://reddit.com/r/bitcointip)" % (txid, transaction_from, transaction_amount, altcurrency_symbol, altcurrency_amount,altcurrency_code, transaction_to)
    rejectedmessage = "[**X**] **Rejected**: [ ~~%s ---> **&#3647;%.8f BTC** *(%s%.2f %s)* ---> %s~~ ](http://reddit.com/r/bitcointip)" % (transaction_from, transaction_amount, altcurrency_symbol, altcurrency_amount,altcurrency_code, transaction_to)

    #create special response for flip
    if (tip_command_flip and cancelmessage==""):
        if (flipresult==1):
            flipmessage = "Bit landed **1** up. %s wins 1 bitcent.\n\n" % (transaction_to)
        if (flipresult==0):
            flipmessage = "Bit landed **0** up. %s wins nothing.\n\n" % (transaction_to)
            rejectedmessage=""
    else:
        flipmessage = ""


    commentreplymessage=""
    #Reply to a comment under what conditions?
    #reply to a flip only if cancelmessage!="" 
    #reply to a +1 internet only if it is a success
    if ((tip_type == "comment") and ((tip_subreddit in _lastallowedsubredditsfetched) or (get_user_gift_amount(transaction_from)>=2)) and (tip_command_verify.lower()!="noverify")):
        #Reply to the comment
        if (flipresult!=-1):
            commentreplymessage += flipmessage
            
        if (txid!="error"):
            commentreplymessage += verifiedmessage
        else:
            commentreplymessage += rejectedmessage

    #if failed +1 internet, don't send an annoying message.
    if (tip_command_internet and cancelmessage):
        commentreplymessage = ""
        
    if (commentreplymessage):
        #if comment reply is prepared, send it
        #enter reply into table
        sql = "INSERT INTO TEST_TABLE_TOSUBMIT (tosubmit_id, type, replyto, subject, text, captchaid, captchasol, sent, timestamp)  VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%f')" % ("", "comment", thing.permalink, "", commentreplymessage, "", "", "0", tip_timestamp)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        
    #TODOif 
    #Send a message to the sender under what conditions?
    #if flipping, only send a pm to sender if they don't have enough for a flip.
    #if +1internet, do not send a pm to sender under any circumstance. (nonusers may use this without intent to tip, don't bother them)
    pmsendermessage=""
    if (cancelmessage!="" or tip_type=="message"):
        #PM the Sender
        if (flipresult!=-1 and txid!="error"):
            pmsendermessage += flipmessage
        if (txid!="error"):
            pmsendersubject = "Successful Bitcointip Notice"
            pmsendermessage += verifiedmessage
        else:
            pmsendersubject = "Failed Bitcointip Notice"
            pmsendermessage += cancelmessage+"\n\n"+ rejectedmessage
        #add footer to PM
        pmsendermessage += get_footer(transaction_from)

    if (tip_command_internet and cancelmessage):
        pmsendermessage = ""
    
    if (pmsendermessage):
        #if pm to sender is prepared, send it
        #enter message into table
        sql = "INSERT INTO TEST_TABLE_TOSUBMIT (tosubmit_id, type, replyto, subject, text, captchaid, captchasol, sent, timestamp)  VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%f')" % ("", "message", transaction_from, pmsendersubject, pmsendermessage, "", "", "0", tip_timestamp)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()

    pmreceivermessage=""
    #Send a message to the receiver under what conditions?
    #only PM receiver if tip_type is a message and success
    if (tip_type == "message" and txid!="error" and tip_command_redditusername):
        #PM the Receiver
        if (flipresult!=-1 and txid!="error"):
            pmreceivermessage += flipmessage
            
        pmreceiversubject = "Bitcointip Notice"
        pmreceivermessage += verifiedmessage 
        #add footer to PM
        pmreceivermessage += get_footer(transaction_to)
        
    if (pmreceivermessage):
        #if pm to receiver is prepared, send it
        #enter message into table
        sql = "INSERT INTO TEST_TABLE_TOSUBMIT (tosubmit_id, type, replyto, subject, text, captchaid, captchasol, sent, timestamp)  VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%f')" % ("", "message", transaction_to, pmreceiversubject, pmreceivermessage, "", "", "0", tip_timestamp)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()


    #if the tip was a comment and replied to, mark as success or fail. 
    if (commentreplymessage):
        if (txid!="error"):
            #upvote it
            thing.upvote()
            print ("Comment Upvoted")
        else:
            #downvote it   
            thing.downvote()
            print ("Comment Downvoted")
            
    if (tip_command):
        #tip found and done
        return 1
    else:
        #no tip in this text
        return 0

    
#find_message_command
#returns text result as message to send back.
def find_message_command(message): #array
    
    returnstring = ""
    
    if (_botstatus == "down" and returnstring==""):
        #if down, just reply with a down message to all messages
        returnstring = "The bitcointip bot is currently down.\n\n[Click here for more information about the bot.](http://www.reddit.com/r/bitcoin/)"
    
    #See if the message author has a bitcointip account, if not, make one for them.
    add_user(message.author.name)
    
    #Start going through the message for commands. Only the first found will be evaluated

    
    
    
    
    ##CHECK FOR MESSAGE TIP (take care of sending all messages here, return empty string, telling eval_messages to not send any more messages. Do this first to avoid redditors with commands in their username.
    if (returnstring==""):
        if (eval_tip(message)):
        #if returns 1, then a tip was found.
        #only do one command per message, so stop looking for more commands
        #messages sent in eval_tip.
            return ""
            
            
            
            

    #"SIGNUP"
    #special first message for those who want one.
    regex_signupmessage = re.compile("(SIGN ?UP)",re.IGNORECASE)
    command_signupmessage = regex_signupmessage.search(message.body)
    
    if (command_signupmessage and returnstring==""):
        returnstring = "Welcome to the bitcointip bot. This is the signup message."
    
    #"REDEEM KARMA: 1thisisabitcoinaddresshereyes"
    #if bitcoinaddress is valid, 
    regex_karmaredeem = re.compile("REDEEM( )?KARMA:( )?(1([A-Za-z0-9]{25,35}))",re.IGNORECASE)
    command_karmaredeem = regex_karmaredeem.search(message.body)
    
    if (command_karmaredeem and returnstring==""):
        
        #karma redemption command found
        karmabitcoinaddress = command_karmaredeem.groups()[2]
        
        #karma limits on which redditors can get bitcoins for their karma
        minlinkkarma = 0
        mincommentkarma = 300
        mintotalkarma = 300

        #baseline amount of bitcoin to give each redditor (enough to cover some mining fees)
        defaultbitcoinamount = 0.00200000

        #get balance of bitcoinfaucet
        faucetbalance = get_user_balance("bitcointipfaucetdepositaddress")
        
        if (not has_user_redeemed_karma(message.author.name)):
            #if not redeemed yet, check for a valid bitcoin address

            print ("user has not redeemed karma yet.")

            if (bitcoind.validateaddress(karmabitcoinaddress)['isvalid']):
            
                #valid bitcoin address detected

                #get user's link karma and comment karms
                print ("Valid bitcoin address detected: ", karmabitcoinaddress)

                linkkarma = message.author.link_karma
                commentkarma = message.author.comment_karma
                totalkarma = linkkarma + commentkarma

                #format all the bitcoin amounts correctly for messages and displaying and storage
                
                #calculate how many bitcoins they might get from karma
                karmabitcoinamount = round((totalkarma/(100000000)),8)
                #print "bitcoin amount: ".number_format($karmabitcoinamount, 8, ".", "");
                
                #only give valid reddit users any bitcoins (check that karma is above a certain amount)
                if ( (linkkarma>minlinkkarma) and (commentkarma>mincommentkarma) and (totalkarma>mintotalkarma)):
                    #User has enough karma
                    print ("user has enough karma")
                    
                    if ( karmabitcoinamount < 0.002 ):
                        bitcoinamount = karmabitcoinamount + defaultbitcoinamount
                        print ("give user defualt amount too.")
                    else:
                        bitcoinamount = karmabitcoinamount
                        print ("don't give user default amount.")

                    #impose limit
                    if (bitcoinamount>0.01):
                        bitcoinamount = 0.01
                    
                    #check to make sure the faucet has enough.
                    if ( faucetbalance > (bitcoinamount + 0.01) ):
                        
                        #The reddit bitcoin faucet has enough
                        print ("the reddit bitcoin faucet has: %.8f BTC", faucetbalance)

                        #go ahead and send the bitcoins to the user
                        txid = bitcoind.transact("bitcointipfaucetdepositaddress", karmabitcoinaddress, bitcoinamount, _txfee)

                        if (txid != "error"):
                            print ("no error, transaction done, bitcoins en route to %s." % (karmabitcoinaddress) )
                            #reply to their message with success
                            returnstring = "Your bitcoins are on their way.  Check the status here: http://blockchain.info/address/%s\n\nIf you do not want your bitcoins, consider passing them on to a [good cause](https://en.bitcoin.it/wiki/Donation-accepting_organizations_and_projects)." % (karmabitcoinaddress)
                            
                            #insert the transaction to the list of TABLE_FAUCET_PAYOUTS
                            sql = "INSERT INTO TEST_TABLE_FAUCET_PAYOUTS (transaction_id, username, address, amount, timestamp) VALUES ('%s', '%s', '%s', '%.8f', '%f')" % (txid, message.author.name, karmabitcoinaddress, bitcoinamount, round(time.time()))
                            _mysqlcursor.execute(sql)
                            _mysqlcon.commit()

                        else:
                            #there was an error with blockchain, have the user try again later maybe.
                            print ("error with the bitcoind.")
                            #say so.
                            returnstring = "The Reddit Bitcoin Faucet is down temporarily.  Try again another day."

                    else:
                        #faucet is out of bitcoins.
                        #say so.
                        returnstring = "The Reddit Bitcoin Faucet is out of bitcoins until someone donates more. View the balance [here](http://blockchain.info/address/13x9weHkPTFL2TogQJz7LbpEsvpQJ1dxfa)."
                    
                else:

                    #user doesn't have enough karma
                    print ("%s doesn't have enough karma." % message.author.name)
                    returnstring = "You do not have enough karma to get bitcoins. You need at least %f Comment Karma to be eligible (You only have %f). Keep redditing or try this bitcoin faucet: https://freebitcoins.appspot.com" % (mincommentkarma, commentkarma)

            else:
                #no valid bitcoin address detected
                print ("No valid bitcon address detected.")
                returnstring = "No valid bitcoin address detected.  Send the string \"REDEEM KARMA: 1YourBitcoinAddressHere\" but put in YOUR bitcoin address."

        else:
            print ("%s has already redeemed karma" % (message.author.name))
            #user has already redeemed karma, can't do it again.
            returnstring = "You have already exchanged your karma for bitcoins.  You can only do this once."
    
    
    #"TRANSACTIONS"/"HISTORY"/"ACTIVITY"
    #Gives use a list of their transactions including deposits/withdrawals/sent/recieved
    regex_history = re.compile("((TRANSACTIONS)|(HISTORY)|(ACTIVITY))",re.IGNORECASE)
    command_history = regex_history.search(message.body)
    
    if (command_history and returnstring==""):
        
        #add first line of transaction table headers to the response.
        transactionhistorymessage = "\n#**%s Transaction History***\n\nDate | Sender | Receiver | BTC | ~USD | Status |\n|:|:|:|:|:|:|\n" % (message.author.name)
        k = 0
        historyrows = []

        sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE sender_username='%s' OR receiver_username='%s' ORDER BY timestamp DESC" % (message.author.name, message.author.name)
        _mysqlcursor.execute(sql)
        result = _mysqlcursor.fetchall()
        for row in result:
            if (k<10):
                sender = row[1]
                receiver_username = row[3]
                receiver_address = row[4]
                amount_BTC = float(row[5])
                amount_USD = float(row[6])
                status = row[13]
                timestamp = float(row[10])
                
                ##if tip is sent directly to address with no username, display address.
                if (receiver_username == ""):
                    receiver = receiver_address
                else:
                    receiver = receiver_username
                
                date = time.strftime("%a %d-%b-%Y", time.gmtime())
                
                if (sender == message.author.name):
                    senderbold = "**"
                    amountsign = "*"
                    receiverbold=""
                    
                elif (receiver == message.author.name):
                    receiverbold = "**"
                    amountsign = "**"
                    senderbold=""
                    
                ##add new transaction row to table being given to user
                historyrows.append("| %s | %s%s%s | %s%s%s | %s&#3647;%.8f%s | %s$%.2f%s | %s |\n" % (date, senderbold, sender, senderbold, receiverbold, receiver, receiverbold, amountsign, amount_BTC, amountsign, amountsign, amount_USD, amountsign, status))

                k+=1 
            elif (k == 10):
                break
            

            ##end
            
        for row in historyrows:
            transactionhistorymessage += row
            
        if (k>=11):
            ##if there are more than 10 transactions, tell them there are some left out after the table.
            transactionhistorymessage = transactionhistorymessage + "*Transaction History Truncated.*\n\n"
            
        #if no transactions, say so
        if (k == 0):
            transactionhistorymessage = "\n\n**You have no transactions.**\n\n"
        else:
            transactionhistorymessage += "\n**Only includes tips to or from your Reddit username.*\n\n\n"
            
        returnstring += transactionhistorymessage




    ###"Gift Amount"
    ###GIFTAMOUNT"
    regex_giftamount = re.compile("(GIFT ?AMOUNT)",re.IGNORECASE)
    command_giftamount = regex_giftamount.search(message.body)
    
    if (command_giftamount and returnstring==""):
        giftamount = get_user_gift_amount(message.author.name)
        returnstring = "You have given /u/bitcointip &#3647;%.8f so far." % (giftamount)
        if (giftamount>=2):
            returnstring = returnstring + "\n\n**Thank you for your support!  Contributors like you make this possible.**"
        elif (giftamount>=1):
            returnstring = returnstring + "\n\nThank you for your support!"
        elif (giftamount>=0.5):
            returnstring = returnstring + "\n\nThank you!"
        elif (giftamount>=0.25):
            returnstring = returnstring + "\n\nThanks!"
        elif (giftamount>0):
            returnstring = returnstring + "\n\nThanks."


    ###"Get a user balance" #Admin only
    ###getbalance:username"
    regex_admingetbalance = re.compile("(getbalance:(.*))",re.IGNORECASE)
    command_admingetbalance = regex_admingetbalance.search(message.body)
    
    if (command_admingetbalance and returnstring==""):
        if (message.author.name.lower()=="nerdfightersean"):
            if (command_admingetbalance.groups()[1]):
                userbalance = get_user_balance(command_admingetbalance.groups()[1])
                returnstring = "%s balance: %f" % (command_admingetbalance.groups()[1], userbalance)
            else:
                returnstring = "error"
        else:
            returnstring = "error"
    


    #Actual export private key
    ###"Export private key"
    ###TRANSFER BALANCE: Y/N"
    regex_exportkey = re.compile("(YES EXPORT PRIVATE KEY)",re.IGNORECASE)
    command_exportkey = regex_exportkey.search(message.body)
    
    if (command_exportkey and returnstring==""):
        if (get_user_gift_amount(message.author.name) >= 0.5):
            print ("Dumping Private key for %s" % (message.author.name))
            privatekey = bitcoind.dumpprivkey(get_user_address(message.author.name))
            if (privatekey!="error"):
                obfuscatedprivatekey = privatekey
                obfuscation = {"1":"(A)",
                            "2":"(B)",
                            "3":"(C)",
                            "4":"(D)",
                            "5":"(E)",
                            "6":"(F)",
                            "7":"(G)",
                            "8":"(H)",
                            "9":"(I)"
                            }
                for key in obfuscation:
                    obfuscatedprivatekey = obfuscatedprivatekey.replace(key, obfuscation[key])
                returnstring = "Your obfuscated (not encrypted) private key is: %s.  To deobfuscate it, replace all the letters in parenthesis with the digit of its position in the English Alphabet.\n\n**Keep it secret. Keep it safe.**" % (obfuscatedprivatekey)
            else:
                returnstring = "There was some kind of error exporting your private key."
        else:
            returnstring = "You have not donated enough to use that command."




    #ask if sure about private key
    ###"Export private key"
    ###TRANSFER BALANCE: Y/N"
    regex_tryexportkey = re.compile("(EXPORT PRIVATE KEY)",re.IGNORECASE)
    command_tryexportkey = regex_tryexportkey.search(message.body)
    
    if (command_tryexportkey and returnstring==""):
        if (get_user_gift_amount(message.author.name) >= 0.5):
            print ("Asking if dump Private key for %s" % (message.author.name))
            returnstring = "Are you sure you want to export your private key?  Anyone (or thing) who knows your private key, can control the bitcoins associated with that bitcoin address.  Make sure you take adequate security considerations.\n\nIf you are sure, reply with YES EXPORT PRIVATE KEY.\n\n(Note: the address will not be in wallet import format yet, so only do this if you know what you are doing.)"
        else:
            returnstring = "You have not donated enough to use that command."

    


    ####################################################################################################################
    #THIS IS DISABLED. IT TAKES LIKE 15 MINUTES TO RESCAN THE BLOCKCHAIN WHEN A NEW KEY IS IMPORTED.
    ###################################################################################################################
    #Let user import a private key to use
    ###"REPLACE PRIVATE KEY WITH: $privatekey
    ###TRANSFER BALANCE: Y/N"
    regex_importkey = re.compile("((REPLACE PRIVATE KEY WITH:)( )?(5[a-zA-Z0-9]{35,60})(( )*(\n)*( )*)(TRANSFER BALANCE:)( )?(Y|N))",re.IGNORECASE)
    command_importkey = regex_importkey.search(message.body)
    
    if (command_importkey and returnstring=="" and False):

        print ("Private Key detected...")
        
        if (get_user_gift_amount(message.author.name) >= 0.5):
        #do it
        
            
            privatekey = command_importkey.groups()[3]
            transfer = command_importkey.groups()[10]
            
            print ("Private Key:", privatekey)
            print ("Transfer:", transfer)
            
            authoroldaddress = get_user_address(message.author.name)
            authoroldbalance = get_user_balance(message.author.name)
            
            print ("authoroldaddress: ", authoroldaddress)
            print ("authoroldbalance: ", authoroldbalance)
            
            
            
            
            importstatus = bitcoind.importprivkey(privatekey, "thisisatemporarylabelthatnobodyshoulduse")
            
            print ("importstatus: ", importstatus)
            
            if (importstatus!="error"):
            
                authornewaddress = bitcoind.getaddressesbyaccount("thisisatemporarylabelthatnobodyshoulduse")[0]
                authornewbalance = bitcoind.getbalance("thisisatemporarylabelthatnobodyshoulduse")
                
                print ("authornewaddress: ", authornewaddress)
                print ("authornewbalance: ", authornewbalance)
            
                setaccountold = bitcoind.setaccount(authoroldaddress, "OLD ADDRESS: "+message.author.name)
                setaccountnew = bitcoind.setaccount(authornewaddress, message.author.name)
                
                print ("setaccountold: ", setaccountold)
                print ("setaccountnew: ", setaccountnew)
                
                if (setaccountold and setaccountnew):
                
                    returnstring = "Replacement successful. Your new bitcoin address is: %s.\n\nYour old bitcoin address was: ~~%s~~." % (authornewaddress, authoroldaddress)
                if (transfer.lower() == "y" and authoroldbalance != 0):
                    moveamount = authoroldbalance - _txfee
                    movedstatus = bitcoind.transact(authoroldaddress, authornewaddress, moveamount, _txfee) 
                    print ("movedstatus: ", movedstatus)
                    if (movedstatus != "error"):
                        returnstring += "\n\nYour old balance of %.8f is being moved to your new address." % (moveamount)
                        authornewbalance += moveamount
                    else:
                        returnstring += "\n\nThere was a problem moving your funds. Either you have too little or something went wrong. Please report if there is a problem."
            
                ##update user table entry with new balance and new address

                sql = "UPDATE TEST_TABLE_USERS SET address='%s' WHERE username='%s'" % (authornewaddress, message.author.name)
                _mysqlcursor.execute(sql)
                _mysqlcon.commit()
                
            else:
                returnstring = "There was a problem setting up your new account. Please report if there is a problem."
        else:
            ##not enough gift.
            returnstring = "You have not donated enough to use that command."   
    
    
    ##ACCEPT PENDING TRANSACTIONS
    ##"ACCEPT"
    regex_accept = re.compile("(ACCEPT)",re.IGNORECASE)
    command_accept = regex_accept.search(message.body)
    
    if (command_accept and returnstring==""):
        set_last_time("LASTACTIVE_"+message.author.name, round(time.time()))
        
        sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE receiver_username='%s' AND status='pending'" % (message.author.name)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        
        returnstring = "Pending tips to you have been accepted."
        
        
        
        
        
    ##DECLINE PENDING TRANSACTIONS
    ##"DECLINE"
    regex_decline = re.compile("(DECLINE)",re.IGNORECASE)
    command_decline = regex_decline.search(message.body)
    
    if (command_decline and returnstring==""):
        set_last_time("LASTACTIVE_"+message.author.name, round(time.time()))
        
        #first in, first returned
        sql = "SELECT * FROM TEST_TABLE_TRANSACTIONS WHERE status='pending' AND receiver_username='%s' ORDER BY timestamp ASC" % (message.author.name)
        _mysqlcursor.execute(sql)
        results = _mysqlcursor.fetchall()
        for row in results:
            transactionid = row[0]
            receiver = row[3]
            sender = row[1]
            timestamp = float(row[10])
            transactionamount = float(row[5])
            

            #try to reverse
            ##check to make sure the reciever has enough
            receiverbalance = get_user_balance(receiver)
            if (receiverbalance >= (transactionamount)):
                ##the receiver has enough, just move the coins from the receiveraddress back to the new senderaddress
                reversalamount = transactionamount - _txfee
                    
                reversalstatus = bitcoind.transact(receiver, sender, reversalamount, _txfee)
                    
                ##mark the transaction as reversed in the table
                if(reversalstatus != "error"):
                    sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='reversed' WHERE transaction_id='%s'" % (transactionid)
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                    print ("Transaction reversed: ", transactionid)
                else:
                    ##the user doesn't have enough to reverse the transaction, they must have spent it in another way.
                    sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE transaction_id='%s'" % (transactionid)
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                    print ("Transaction completed (user already spent funds):", transactionid)
            else:
                ## the receiver doesn't have enough.  They must have already spent it
                ##mark as completed instead of reversed.
                sql = "UPDATE TEST_TABLE_TRANSACTIONS SET status='completed' WHERE transaction_id='%s'" % (transactionid)
                _mysqlcursor.execute(sql)
                _mysqlcon.commit()
                print ("Transaction completed (user already spent funds):", transactionid)
    
        returnstring = "Pending tips to you have been returned to sender if possible."
        
        
    ##HELP
    regex_help = re.compile("(HELP)",re.IGNORECASE)
    command_help = regex_help.search(message.body)
    
    if (command_help and returnstring==""):
        returnstring = "Check the /r/bitcointip subreddit for updates and announcements or the [Help Page](http://www.reddit.com/r/bitcointip) for a list of commands."
        
        
    ##NO COMMAND FOUND DO YOU NEED HELP?
    if (returnstring == ""):    
        returnstring = "No command was found in your message.\n\nTo fund your account, send bitcoins to your Deposit Address.\n\nFor help with commands, see [This Page](http://www.reddit.com/r/test/comments/11iby2/bitcointip_tip_redditors_with_bitcoin/).\n\nFor other news, see the /r/bitcointip subreddit."
        
        

    ##ALL MESSAGES ADD FOOTER TO END OF ANY MESSAGE
        
    returnstring += get_footer(message.author.name)


    if (returnstring):
        ##return returnstring;
        returnsubject = "Re: " + message.subject
        #insert returnstring into TEST_TABLE_TOSUBMIT
        #enter message into table
        sql = "INSERT INTO TEST_TABLE_TOSUBMIT (tosubmit_id, type, replyto, subject, text, captchaid, captchasol, sent, timestamp)  VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%f')" % ("", "message", message.author.name, returnsubject, returnstring, "", "", "0", message.created_utc)
        _mysqlcursor.execute(sql)
        _mysqlcon.commit()
        print("To:",message.author.name)
        print (returnsubject)
        #print (returnstring)
    
    



#eval_messages
#get new messages and go through each one looking for a command, then respond.
def eval_messages():
    print ("Checking Messages...")
    
    global _lastmessageevaluated
    global _lastmessageevaluatedtime
    
    #get some unread messages.
    newest_message_evaluated_time = 0
    
    unread_messages = _reddit.user.get_unread(limit=1000)
    for message in unread_messages:
        if (not message.was_comment):
            #ignore self messages and bannedusers messages/comments
            if ((message.author.name.lower() != "bitcointip") and (message.author.name.lower() not in _lastbannedusersfetched)): 
                message.body = message.body.encode("ascii", "xmlcharrefreplace").decode("ascii", "xmlcharrefreplace")
                print ("Message %s: %s" % (message.author.name, message.subject))
                #check message for command and reply
                find_message_command(message)
                #mark as read
                message.mark_as_read()
                if (message.created_utc>newest_message_evaluated_time):
                    newest_message_evaluated_time = round(message.created_utc)
            else:
                print ("IGNORE MESSAGE (outgoing)")
                message.mark_as_read()
                if (message.created_utc>newest_message_evaluated_time):
                    newest_message_evaluated_time = round(message.created_utc)
        else:
            print ("IGNORE MESSAGE (comment reply)")
            message.mark_as_read()
            if (message.created_utc>newest_message_evaluated_time):
                    newest_message_evaluated_time = round(message.created_utc)
            
    if (newest_message_evaluated_time):
        _lastmessageevaluated = newest_message_evaluated_time
        set_last_time("lastmessageevaluated", _lastmessageevaluated)
        
    _lastmessageevaluatedtime = round(time.time())
    set_last_time("lastmessageevaluatedtime",_lastmessageevaluatedtime)
    

#find_comment_command
#find a command in a user comment
def find_comment_command(comment):
    eval_tip(comment)




#eval_comments
# get new comments and go through each one looking for a command, then respond.
def eval_comments():
    print ("Checking Comments...")
    
    global _lastcommentevaluatedtime
    global _lastcommentevaluated
    global _lastfriendcommentevaluatedtime
    global _lastfriendcommentevaluated
    
    multiredditstring = ""
    for x in _lastallowedsubredditsfetched:
        multiredditstring += x + "+"
    
    multi_reddits = _reddit.get_subreddit(multiredditstring)
    
    #go through comments of allowed subreddits but NOT friendsofbitcointip
    _lastcommentevaluatedtime = get_last_time("lastcommentevaluatedtime")
    
    first_comment_this_loop = None
    print ("checking comments")
    multi_reddits_comments = multi_reddits.get_comments(limit=1000)
    for comment in multi_reddits_comments:
        if (not first_comment_this_loop):
            first_comment_this_loop = round(comment.created_utc)
        if (comment.created_utc <= _lastcommentevaluated):
            print ("old comment reached")
            break
        else:
            if ((comment.author.name.lower() not in _lastfriendsofbitcointipfetched) and (comment.author.name.lower() not in _lastbannedusersfetched) and comment.author.name.lower()!="bitcointip"):#exclude friendsofbitcointip and banned users
                comment.body = comment.body.encode("ascii", "xmlcharrefreplace").decode("ascii", "xmlcharrefreplace")
                print (("("+comment.subreddit.display_name+")"+comment.author.name+":"+comment.body))
                find_comment_command(comment)
    _lastcommentevaluated = first_comment_this_loop
    _lastcommentevaluatedtime = round(time.time())
    #write updated lastcommentevaluatedtimestamp to table.
    set_last_time("lastcommentevaluated", _lastcommentevaluated)
    set_last_time("lastcommentevaluatedtime", _lastcommentevaluatedtime)
    
     
    #now go through friendsofbitcointip separately
    
    _lastfriendcommentevaluatedtime = get_last_time("lastfriendcommentevaluatedtime")
    friends_reddit = _reddit.get_subreddit("friends")
    
    first_comment_this_loop = None
    print ("checking friend comments")
    friends_reddit_comments = friends_reddit.get_comments(limit=1000)
    for comment in friends_reddit_comments:
        if (not first_comment_this_loop):
            first_comment_this_loop = round(comment.created_utc)
        if (comment.created_utc <= _lastfriendcommentevaluated):
            print ("old friend comment reached")
            break
        else:
            comment.body = comment.body.encode("ascii", "xmlcharrefreplace").decode("ascii", "xmlcharrefreplace")
            print (("("+comment.subreddit.display_name+")"+comment.author.name+":"+comment.body))
            find_comment_command(comment)
    _lastfriendcommentevaluated = first_comment_this_loop
    #write updated lastfriendcommentevaluatedtimestamp to table.
    _lastfriendcommentevaluatedtime = round(time.time())
    set_last_time("lastfriendcommentevaluatedtime", _lastfriendcommentevaluatedtime)
    set_last_time("lastfriendcommentevaluated", _lastfriendcommentevaluated)


#submit_messages
#submits outgoing messages/comments to reddit.com
def submit_messages():
    print ("Submitting Messages and comment replies...")
    
    #go through each entry, and try to submit reply.
    #if reply is sent out, mark message as sent=1.
    #if reply is not sent because of error, mark as sent=x.

    going = True
    
    ##go through list of tosubmit orderby timestamp from oldest to newest
    sql = "SELECT * FROM TEST_TABLE_TOSUBMIT WHERE sent='0' ORDER BY timestamp ASC"
    _mysqlcursor.execute(sql)
    result = _mysqlcursor.fetchall()
    for row in result:
        if (going):
            print ("Trying to go through each unsent message/comment")
            thingtype = row[1]
            replyto = row[2] #user if type=message, permalink if type=comment
            subject = row[3]
            text = row[4]
            captchaid = row[5]
            captchasol = row[6]
            sent = float(row[7])
            timestamp = float(row[8])
            
            print ("Type:", thingtype)
            
            if ( thingtype == "comment" ): 
                comment = _reddit.get_submission(replyto).comments[0]
                
                try:
                    comment.reply(text)
                    print ("Comment Sent")
                    ##it worked.
                    sql = "UPDATE TEST_TABLE_TOSUBMIT SET sent=1 WHERE type='%s' AND timestamp='%f' AND replyto='%s'" % (thingtype, timestamp, replyto)
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                    print ("Comment Marked as delivered")
                    
                except Exception as e:
                    print ("Error:",e)
                    print ("Comment not delivered...skipping for now.")
                

            if ( thingtype == "message" ): 
                
                #try to send a personal message
                try:
                    _reddit.send_message(replyto,subject,text)
                    print ("message sent")
                    sql = "UPDATE TEST_TABLE_TOSUBMIT SET sent=1 WHERE type='%s' AND timestamp='%f' AND replyto='%s'" % (thingtype, timestamp, replyto)
                    _mysqlcursor.execute(sql)
                    _mysqlcon.commit()
                    print ("Message marked as delivered")
                        
                except Exception as e:
                    print ("message not sent", e)
                    if (e == "Error `that user doesn't exist` on field `to`"):
                        #user doesn't exist, cancel the message
                        sql = "UPDATE TEST_TABLE_TOSUBMIT SET sent=x WHERE type='%s' AND timestamp='%f' AND replyto='%s'" % (thingtype, timestamp, replyto)
                        _mysqlcursor.execute(sql)
                        _mysqlcon.commit()
                        print ("user doesn't exist. message cancelled.")

                
                    


def exitpeacefully(e):
    print ("Exiting Peacefully")
    
    #LOCK BITCOIND WALLET AT PROGRAM END
    print ("Locking Bitcoin Wallet")
    print (bitcoind.walletlock())

    #The bot has had a problem and quit. Email the admin for help:
    errorstring = ("Error, the bot has stopped running!\n\n\nException:",str(e))
    print ("Emailing Admin")
    #email admin alert
    emailcommand = 'echo "The bot has stopped.\n\n Error:\n\n" | mutt -s "ALERT: BOT HAS STOPPED" -- root '+_adminemail
    print (emailcommand)
    result = subprocess.call(emailcommand, shell=True)
    
    #then back up the wallet:
    datetime = time.strftime("%a_%Y-%b-%d_%H:%M:%S", time.gmtime())
    result = bitcoind.backupwallet("/root/backups/bitcointip_wallet_%s.dat" % (datetime))
    result = bitcoind.backupwallet("/root/backups/bitcointip_wallet.dat" % (datetime))
    print ("Backed up wallet")

    #then backup the mysql database:
    backupmysqlcommand = "mysqldump --user "+_MYSQLlogin+" --password="+_MYSQLpass+" bitcointip > /root/backups/bitcointip_db.sql"
    backupmysqldatedcommand = "mysqldump --user "+_MYSQLlogin+" --password="+_MYSQLpass+" bitcointip > /root/backups/bitcointip_db_`date +%a_%Y-%b-%d_%H:%M:%S`.sql"
    result = subprocess.call(backupmysqlcommand, shell=True)
    result = subprocess.call(backupmysqldatedcommand, shell=True)
    print ("Backed up mysql db")
    exit(0)

    
def createbackups():
    #back up the wallet:
    datetime = time.strftime("%a_%Y-%b-%d_%H:%M:%S", time.gmtime())
    result = bitcoind.backupwallet("/root/backups/bitcointip_wallet_%s.dat" % (datetime))
    result = bitcoind.backupwallet("/root/backups/bitcointip_wallet.dat")
    print ("Backed up wallet")

    #then backup the mysql database:
    backupmysqlcommand = "mysqldump --user "+_MYSQLlogin+" --password="+_MYSQLpass+" bitcointip > /root/backups/bitcointip_db.sql"
    backupmysqldatedcommand = "mysqldump --user "+_MYSQLlogin+" --password="+_MYSQLpass+" bitcointip > /root/backups/bitcointip_db_`date +%a_%Y-%b-%d_%H:%M:%S`.sql"
    result = subprocess.call(backupmysqlcommand, shell=True)
    result = subprocess.call(backupmysqldatedcommand, shell=True)
    print ("Backed up mysql db")
    _lastbackuptime = round(time.time())
    set_last_time("lastbackuptime", _lastbackuptime)



######################################################################
#MAIN
######################################################################
#DETAILS:
_MYSQLhost = "???"
_MYSQLlogin = "???"
_MYSQLpass = "???"
_MYSQLdbname = "???"
_MYSQLport = "???"

_BITCOINDlogin = "???"
_BITCOINDpass = "???"
_BITCOINDip = "???"
_BITCOINDport = "???"
_BITCOINDsecondpass = "???"

_REDDITbotusername = "???"
_REDDITbotpassword = "???"
_REDDITuseragent = "???"

_adminemail = "???"


# BOTSTATUS (DOWN/UP)
_botstatus = "up"


#update exchange rate from the charts every 3 hours
_intervalupdateexchangerate = 60*60*3
#update transactions (pending->completed or pending->cancelled) every 24 hours
_intervalpendingupdate = 60*60*24*1
#update transactions (pending->cancelled) when transactions are 21 days old
#60 days to start with.
_intervalpendingcancel = 60*60*24*60
#notify users that they have a pending transaction for them every 7 days.
_intervalpendingnotify = 60*60*24*7


# CONNECT TO MYSQL DATABASE
try:
    _mysqlcon = pymysql.connect(host=_MYSQLhost, port=_MYSQLport, user=_MYSQLlogin, passwd=_MYSQLpass, db=_MYSQLdbname, use_unicode=True, charset='utf8')
    _mysqlcursor = _mysqlcon.cursor()
    print ("Connected to MYSQL.")
except Exception as e:
    exitpeacefully(e)



# CONNECT TO BITCOIND SERVER
try:
    _jsonRPCClientString = "http://"+_BITCOINDlogin+":"+_BITCOINDpass+"@"+_BITCOINDip+":"+_BITCOINDport+"/"
    bitcoind.access = ServiceProxy(_jsonRPCClientString)
    print("Connected to BITCOIND.")
    if (bitcoind.getinfo()=="error"):
        exitpeacefully()
except Exception as e:
    exitpeacefully(e)


    
# CONNECT TO REDDIT.COM
try:
    _reddit = praw.Reddit(user_agent = _REDDITuseragent)
    _reddit.login(_REDDITbotusername, _REDDITbotpassword)
    print("Connected to REDDIT.")
except Exception as e:
    exitpeacefully(e)


#TIMINGS

#LAST TIME THIS WAS DONE (Make default to right now to avoide double evaluations)
_lastcommentevaluatedtime = round(time.time())
_lastfriendcommentevaluatedtime = round(time.time())
_lastmessageevaluatedtime = round(time.time())
_lastallowedsubredditsfetchedtime = round(time.time())
_lastfriendsofbitcointipfetchedtime = round(time.time())
_lastbannedusersfetchedtime = round(time.time())
_lastexchangeratefetchedtime = round(time.time())
_lastpendingupdatedtime = round(time.time())
_lastpendingnotifiedtime = round(time.time())
_lastbackuptime = round(time.time())

_lastcommentevaluatedtime = get_last_time("lastcommentevaluatedtime")
_lastfriendcommentevaluatedtime = get_last_time("lastfriendcommentevaluatedtime")
_lastmessageevaluatedtime = get_last_time("lastmessageevaluatedtime")
_lastallowedsubredditsfetchedtime = get_last_time("lastallowedsubredditsfetchedtime")
_lastfriendsofbitcointipfetchedtime = get_last_time("lastfriendsofbitcointipfetchedtime")
_lastbannedusersfetchedtime = get_last_time("lastbannedusersfetchedtime")
_lastexchangeratefetchedtime = get_last_time("lastexchangeratefetchedtime")
_lastpendingupdatedtime = get_last_time("lastpendingupdatedtime")
_lastpendingnotifiedtime = get_last_time("lastpendingnotifiedtime")
_lastbackuptime = get_last_time("lastbackuptime")

_lastcommentevaluated = get_last_time("lastcommentevaluated")
_lastfriendcommentevaluated = get_last_time("lastfriendcommentevaluated")
_lastmessageevaluated = get_last_time("lastmessageevaluated")
_lastallowedsubredditsfetched = get_last_time("lastallowedsubredditsfetched")
_lastfriendsofbitcointipfetched = get_last_time("lastfriendsofbitcointipfetched")
_lastbannedusersfetched = get_last_time("lastbannedusersfetched")
_lastexchangeratefetched = get_last_time("lastexchangeratefetched")
_lastpendingupdated = get_last_time("lastpendingupdated")
_lastpendingnotified = get_last_time("lastpendingnotified")


#if first time, don't retroactively read things.
if (_lastcommentevaluatedtime==0):
    _lastcommentevaluatedtime = round(time.time())
    set_last_time("lastcommentevaluatedtime", _lastcommentevaluatedtime)
if (_lastfriendcommentevaluatedtime==0):
    _lastfriendcommentevaluatedtime = round(time.time())
    set_last_time("lastfriendcommentevaluatedtime", _lastfriendcommentevaluatedtime)
if (_lastmessageevaluatedtime==0):
    _lastmessageevaluatedtime = round(time.time())
    set_last_time("lastmessageevaluatedtime", _lastmessageevaluatedtime)
if (_lastpendingupdatedtime==0):
    _lastpendingupdatedtime = round(time.time())
    set_last_time("lastpendingupdatedtime", _lastpendingupdatedtime)
if (_lastpendingnotifiedtime==0):
    _lastpendingnotifiedtime = round(time.time())
    set_last_time("lastpendingnotifiedtime", _lastpendingnotifiedtime)


#get list of allowed subreddits by checking bitcointip's reddits/mine
_lastallowedsubredditsfetched = []
refresh_allowed_subreddits()

#get list of friends from reddit
_lastfriendsofbitcointipfetched = []
refresh_friends()

#get list of banned users from reddit
_lastbannedusersfetched = []
refresh_banned_users()

#get tx fee from bitcoind
_txfee = 0.0005
print ("Transaction fee is %f" % (_txfee))

#Initialize Exchange rates for first time
if (not _lastexchangeratefetched):
    _lastexchangeratefetched = { "XBC":1, "CBC":100, "MBC":1000, "UBC":1000000, "SBC":100000000, 'USD':0, 'AUD':0, 'CAD':0, 'EUR':0, 'JPY':0, 'GBP':0}

refresh_exchange_rate()

print (_lastexchangeratefetched)

try:
    # WHILE THE BOT DOESN'T HAVE ANY PROBLEMS, KEEP LOOPING OVER EVALUATING COMMENTS, MESSAGES, AND SUBMITTING REPLIES
    while (True):

        start_loop_time = round(time.time())

        #UNLOCK BITCOIND WALLET
        print ("Unlocking Bitcoin Wallet...")
        print  (bitcoind.walletpassphrase(_BITCOINDsecondpass, 6000))


        #CHECK/UPDATE EXCHANGE RATE
        refresh_exchange_rate()

        #CHECK FOR NEW REDDIT PERSONAL MESSAGES
        eval_messages()

        #CHECK FOR NEW COMMENTS
        if (_botstatus == "up"): #if down, don't check comments
            eval_comments()

        #UPDATE PENDING TRANSACTIONS
        if (_botstatus == "up"): #if down, don't update pending transactions
            update_transactions()

        #LOCK BITCOIND WALLET
        print ("Locking Bitcoin Wallet")
        print (bitcoind.walletlock())
        
        #SUBMIT MESSAGES IN OUTBOX TO REDDIT
        submit_messages()

        #if the loop took less than 10 minutes, sleep for 5 min.
        if (round(time.time())<(start_loop_time+600)):
            print ("Sleeping for 5 min...")
            time.sleep(300)

            
        #todo every 24 hours, backup the wallet.
        if (round(time.time())>(_lastbackuptime+(24*60*60))):
            createbackups()

    #LOCK BITCOIND WALLET AT PROGRAM END
    print ("Locking Bitcoin Wallet")
    print (bitcoind.walletlock())
except Exception as e:

    exitpeacefully(e)
