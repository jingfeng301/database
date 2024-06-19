Sell-ebrate is an online retail management application that performs basic online retail functions such as selling and facilitating the management of products and users.

Online retail management applications are much more convenient than conventional physical retail stores due to the convenience and scalability of the retailing to customers. Online retail management applications are centralized and allow complex functionality such as analyzing data and adjustment of prices as compared to conventional retail stores that are difficult to facilitate the selling of products as each store has their own inventory to manage.

Hence, Sell-ebrate seeks to sell and manage products using a web application to create users, update the inventory and price of products as well as being capable of complex functions such as predicting future sales based on past sales trends.

# Dependencies

Copy and paste .env.template to .env and update your DB credentials in .env

```
pip install django django-environ mysqlclient

python manage.py migrate
```

## Create a new table inside your DB

```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
```

Please do python manage.py migrate to add in Product Description. Miss out on this.

## Seed Database with Dataset

Copy and paste the script in your database CLI and run it to seed your database.

# Local Development

```
python manage.py runserver
```

```
./Sellebrate/myapp/migrations/seed.sql
```

# To Do

1. Write out instruction on how to use this app in README
2. Insert in CRUD Ops inside Views.py
