# encoding: UTF-8
# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your
# database schema. If you need to create the application database on another
# system, you should be using db:schema:load, not running all the migrations
# from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended to check this file into your version control system.

ActiveRecord::Schema.define(:version => 20130407183105) do

  create_table "messages", :force => true do |t|
    t.string   "type"
    t.string   "reply"
    t.text     "subject"
    t.text     "body"
    t.string   "captcha_id"
    t.string   "captcha_sol"
    t.boolean  "sent"
    t.datetime "created_at",  :null => false
    t.datetime "updated_at",  :null => false
  end

  create_table "transactions", :force => true do |t|
    t.string   "transaction_id"
    t.string   "sender_user_name"
    t.string   "sender_user_address"
    t.string   "receiver_user_name"
    t.string   "receiver_user_address"
    t.decimal  "amount_btc"
    t.decimal  "amount_usd"
    t.string   "type"
    t.string   "url"
    t.string   "subreddit"
    t.datetime "verified_at"
    t.string   "status_message"
    t.string   "status"
    t.datetime "created_at",            :null => false
    t.datetime "updated_at",            :null => false
  end

  create_table "users", :force => true do |t|
    t.string   "reddit_user_name"
    t.string   "uuid"
    t.string   "bitcoin_address"
    t.decimal  "balance"
    t.decimal  "total_gift_amount"
    t.datetime "created_at",        :null => false
    t.datetime "updated_at",        :null => false
  end

end
