class CreateUsers < ActiveRecord::Migration
  def self.up
    create_table :users do |t|
      t.string :user_name
      t.string :address
      t.decimal :balance
      t.decimal :total_gift_amount

      t.timestamps
    end
  end

  def self.down
    drop_table :users
  end
end
