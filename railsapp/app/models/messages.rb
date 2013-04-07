class Messages < ActiveRecord::Base
  attr_accessible :body, :captcha_id, :captcha_sol, :reply, :sent, :subject, :type
end
