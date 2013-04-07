require 'pry'
namespace :contacts do
  task :import => :environment do
    puts 'test'
    reddit = Snoo::Client.new

    reddit.log_in ENV['REDDIT_USERNAME'], ENV['REDDIT_PASSWORD']
    messages = reddit.get_messages
    p messages
    binding.pry
  end
end
