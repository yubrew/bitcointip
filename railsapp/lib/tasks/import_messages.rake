require 'pry'

namespace :users do
  task :process_reddit => :environment do
    messages = import_reddit_messages
    if messages
      names = get_potential_users(messages)
      names.each do |name|
        User.where(reddit_user_name: name).first_or_create
      end
    end
  end

  def import_reddit_messages
    reddit = Snoo::Client.new

    reddit.log_in ENV['REDDIT_USERNAME'], ENV['REDDIT_PASSWORD']
    messages = reddit.get_messages['data']['children']
  end

  def get_potential_users(messages)
    users = messages.map{|x| x['data']['author'] if x['kind'] == 't4'} if messages
    #users = ['john','bob','billy']
    users
  end
end
