require 'spec_helper'

describe User do
  pending "add some examples to (or delete) #{__FILE__}"

  context 'user validation' do
    it 'should not save if user_name is nil' do
      user = User.new(reddit_user_name: nil)
      user.should_not be_valid
    end

    it 'should not create user with duplicate user_name' do
      User.create(reddit_user_name: 'john')
      duplicate_user = User.new(reddit_user_name: 'john')
      duplicate_user.should_not be_valid
    end

    it 'should create user with valid info' do
      valid_user = User.new(reddit_user_name: 'john')
      valid_user.should be_valid
    end
  end

  context 'check pre_save' do
  end

  context 'check post_save' do
  end
end
