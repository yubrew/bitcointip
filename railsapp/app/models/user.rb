class User < ActiveRecord::Base
  attr_accessible :reddit_user_name, :uuid, :bitcoin_address, :balance, :total_gift_amount
  validates :reddit_user_name, presence: true, uniqueness: true

  before_save :pre_save
  after_save :post_save

  private
    def pre_save
      self.uuid = UUID::generate
      #self.address = BitcoinWrapper.create_address
    end

    def post_save
      #CommunicationWrapper.send_account_creation_message(self.uuid)
    end
end
