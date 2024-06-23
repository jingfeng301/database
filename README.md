Sell-ebrate is an online retail management application that performs basic online retail functions such as selling and facilitating the management of products and users.

Online retail management applications are much more convenient than conventional physical retail stores due to the convenience and scalability of the retailing to customers. Online retail management applications are centralized and allow complex functionality such as analyzing data and adjustment of prices as compared to conventional retail stores that are difficult to facilitate the selling of products as each store has their own inventory to manage.

Hence, Sell-ebrate seeks to sell and manage products using a web application to create users, update the inventory and price of products as well as being capable of complex functions such as predicting future sales based on past sales trends.

# Dependencies

Copy and paste .env.template to .env and update your DB credentials in .env

```
pip install django django-environ mysqlclient tabulate pandas

python manage.py migrate
```

## Seed Database with Dataset

Import the seed script to your database

```
mysql -u username -p database_name < "./Sellebrate/myapp/migrations/seed.sql"
```

# Local Development

```
python manage.py runserver
```
