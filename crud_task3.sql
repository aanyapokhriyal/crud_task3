create database crud_task3;
use crud_task3;

create table user_accounts(
id int auto_increment primary key,
email varchar(100) unique not null,
hashed_password varchar(100) not null,
created_at timestamp default current_timestamp,
role varchar(10) );

CREATE TABLE user_details (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_name VARCHAR(100) NOT NULL,
  dob DATE NOT NULL,
  course VARCHAR(50) NOT NULL,
  phone VARCHAR(15) NOT NULL,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES user_accounts(id)
);
select * from  user_details;
select * from  user_accounts;
UPDATE user_accounts SET role = 'admin'  WHERE email = 'admin@gm.com';
UPDATE user_accounts SET role = 'superadmin'  WHERE email = 'superadmin@gm.com';