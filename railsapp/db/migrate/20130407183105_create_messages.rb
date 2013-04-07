class CreateMessages < ActiveRecord::Migration
  def change
    create_table :messages do |t|
      t.string :type
      t.string :reply
      t.text :subject
      t.text :body
      t.string :captcha_id
      t.string :captcha_sol
      t.boolean :sent

      t.timestamps
    end
  end
end
