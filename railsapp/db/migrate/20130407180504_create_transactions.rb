class CreateTransactions < ActiveRecord::Migration
  def self.up
    create_table :transactions do |t|
      t.string :transaction_id
      t.string :sender_user_name
      t.string :sender_user_address
      t.string :receiver_user_name
      t.string :receiver_user_address
      t.decimal :amount_btc
      t.decimal :amount_usd
      t.string :type
      t.string :url
      t.string :subreddit
      t.datetime :verified_at
      t.string :status_message
      t.string :status

      t.timestamps
    end
  end

  def self.down
    drop_table :transactions
  end
end
