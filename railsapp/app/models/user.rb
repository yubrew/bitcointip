class User < ActiveRecord::Base
  attr_accessible :user_name, :address, :balance, :total_gift_amount
end
