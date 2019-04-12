# Item Catalog Web App
This web app is a project for the Udacity [FSND Course](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

## About
This project is  a website to know the an information about the all mobiles in the market.different brands and each brand mobiles names,cost,diascription and etc. It is a RESTful web application utilizing the Flask framework which accesses a SQL database that populates categories and their items. OAuth2 provides authentication for further CRUD functionality on the application. Currently OAuth2 is implemented for Google Accounts. Only the loged in user can manuplate the database, unlike others who can just see the content. User may create a brand as well as mobiles in any of the brands. The user can delete his own mobile but not other's mobiles. The user cannot delete brand, because there may be many mobiles of other users in that brand.

## In This Repo
This project has one main Python module `projects.py` which runs the Flask application. A SQL database is created using the `database_setup.py` module.
The Flask application uses stored HTML templates in the tempaltes folder to build the front-end of the application.

## Skills Honed
1. Python
2. HTML
3. CSS
4. OAuth
5. Flask Framework

## Installation
There are some dependancies and a few instructions on how to run the application.

## Dependencies
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

## How to Install
1. Install Vagrant & VirtualBox
2. Clone the Udacity Vagrantfile
3. Go to Vagrant directory and either clone this repo or download and place zip here
3. Launch the Vagrant VM (`vagrant up`)
4. Log into Vagrant VM (`vagrant ssh`)
5. Navigate to `cd/vagrant` as instructed in terminal
6. The app imports requests which is not on this vm. Run sudo pip install requests
7. Setup application database `python database_setup.py`
8. Run application using `python projects.py`
9. Access the application locally using http://localhost:8000


*Optional step(s)
## Using Google Login
To get the Google login working there are a few additional steps:
1. Go to [Google Dev Console](https://console.developers.google.com)
2. Sign up or Login if prompted
3. Go to Credentials
4. Select Create Crendentials > OAuth Client ID
5. Select Web application
6. Enter name 'Item-Catalog'
7. Authorized JavaScript origins = 'http://localhost:8000'
8. Authorized redirect URIs = 'http://localhost:8000/login' && 'http://localhost:8000/gconnect'
9. Select Create
10. Copy the Client ID and paste it into the `data-clientid` in login.html
11. On the Dev Console Select Download JSON
12. Rename JSON file to client_secrets.json
13. Place JSON file in item-catalog directory that you cloned from here
14. Run application using `python projects.py`

## json end points
The following are open to the public:

1. '/brand/json'
    -displays all the brands information.
2. '/brand/<int:brand_id>/mobile/json'
    -displays the all  mobiles in specific brand.

