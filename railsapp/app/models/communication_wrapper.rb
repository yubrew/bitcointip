class CommunicationWrapper
  attr_accessor :reddit_client, :messages, :last_checked_at, :last_message_id

  def initialize
    self.reddit_client = Snoo::Client.new
  end

  def get_messages
    reddit_client.log_in ENV['REDDIT_USERNAME'], ENV['REDDIT_PASSWORD'] unless reddit_client.logged_in?
    self.messages = reddit_client.get_messages['data']['children']
    set_last(messages.last)
  end

  def send_message(to, subject, text)
    reddit_client.log_in ENV['REDDIT_USERNAME'], ENV['REDDIT_PASSWORD'] unless reddit_client.logged_in?
    reddit_client.send_pm to, subject, text
  end

  def set_last(message)
    last_message = message['kind'] + '_' + message['data']['id']
    last_checked_at = Time.zone.now
  end

  def send_welcome_message(uuid)
    subject = "create your bitcointips account"
    message = "Hi #{user.user_name},\nYou've been approved for a bitcointips account. Remember, this is a beta project, only send what you're not afraid to lose! Send some bitcoin to your address: #{user.bitcoin_address}. If you have any questions, feel free to PM me. Also please look on the github project wiki.\n~yubrew"
    user = User.where(uuid: uuid).first
  end
end
