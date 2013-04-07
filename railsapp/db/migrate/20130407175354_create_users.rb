class CreateUsers < ActiveRecord::Migration
  def change
    create_table :users do |t|
      t.string :username
      t.string :address
      t.decimal :balance
      t.decimal :gift_amount

      t.timestamps
    end
  end
end
