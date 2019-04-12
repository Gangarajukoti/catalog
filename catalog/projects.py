from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import url_for
from flask import flash


from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Brand, Mobile, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "online_mobiles"


# Connect to Database and create database session
engine = create_engine('sqlite:///mobiledb.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# JSON APIs to view brands Information


@app.route('/brand/json')
def brandjson():
    brand = session.query(Brand)
    return jsonify(brands=[i.serialize for i in brand])


@app.route('/brand/<int:brand_id>/mobile/json')
def mobilesJson(brand_id):
    mob = session.query(Mobile).filter_by(brand_id=brand_id).all()
    return jsonify(mobiles=[i.serialize for i in mob])


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# GConnect


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output
# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    print(email)
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        print("in getUserID exception")
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/brand/')
def showBrand():
    brand = session.query(Brand).all()
    if 'username' not in login_session:
        return render_template('publicbrands.html', brands=brand)
    else:
        owner = getUserID(login_session['email'])
        return render_template('brands.html', brands=brand, owner=owner)


@app.route('/brand/new/', methods=['GET', 'POST'])
def newBrand():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newBrand = Brand(
            name=request.form['name'],
            pic=request.form['pic'],
            description=request.form['description'],
            user_id=login_session['user_id'])
        session.add(newBrand)
        session.commit()
        return redirect(url_for('showBrand'))
    else:
        return render_template('newBrand.html')


@app.route('/brand/<int:brand_id>/edit/', methods=['GET', 'POST'])
def editBrand(brand_id):
    editedBrand = session.query(Brand).filter_by(id=brand_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editedBrand.user_id != login_session['user_id']:
        flash('your not authorized to edit brand.')
        return render_template('newBrand.html')

    if request.method == 'POST':
        if request.form['name']:
            editedBrand.name = request.form['name']
        if request.form['pic']:
            editedBrand.image = request.form['pic']
        if request.form['description']:
            editedBrand.description = request.form['description']
        session.commit()
        flash('brand Successfully Edited %s' % editedBrand.name)
        return redirect(url_for('showBrand'))
    else:
        return render_template('editBrand.html', brand=editedBrand)


@app.route('/brand/<int:brand_id>/delete/', methods=['GET', 'POST'])
def deleteBrand(brand_id):
    brandToDelete = session.query(Brand).filter_by(id=brand_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if brandToDelete.user_id != login_session['user_id']:
        flash('your not authorized to delete brand.')
        return render_template('newBrand.html')

    if request.method == 'POST':
        session.delete(brandToDelete)
        flash('%s Successfully Deleted' % brandToDelete.name)
        session.commit()
        return redirect(url_for('showBrand', brand_id=brand_id))
    else:
        return render_template('deleteBrand.html', brand=brandToDelete)


@app.route('/brand/<int:brand_id>/')
@app.route('/brand/<int:brand_id>/mobile/')
def showMobile(brand_id):
    brand = session.query(Brand).filter_by(id=brand_id).one()
    creator = getUserInfo(brand.user_id)
    items = session.query(Mobile).filter_by(brand_id=brand_id).all()
    print(items)
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        print("not in login session")
        return render_template('publicmobile.html',
                               items=items, brand=brand, creator=creator)
    else:
        print("in login session")
        return render_template('mobile.html',
                               items=items, brand=brand, creator=creator)


@app.route('/brand/<int:brand_id>/mobile/new/', methods=['GET', 'POST'])
def newMobile(brand_id):
    if 'username' not in login_session:
        return redirect('/login')
    brand = session.query(Brand).filter_by(id=brand_id).one()
    if request.method == 'POST':
        print("in post method")
        newItem = Mobile(
            name=request.form['name'],
            description=request.form['description'],
            image=request.form['image'],
            price=request.form['price'],
            rating=request.form['rating'],
            offer=request.form['offer'],
            brand_id=brand_id,
            user_id=getUserID(
                login_session['email']))
        session.add(newItem)
        session.commit()
        flash('New Mobile %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMobile', brand_id=brand_id))
    else:
        return render_template('newmobileitem.html', brand_id=brand_id)


@app.route('/brand/<int:brand_id>/mobile/<int:mobile_id>/edit',
           methods=['GET', 'POST'])
def editMobile(brand_id, mobile_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Mobile).filter_by(id=mobile_id).one()
    brand = session.query(Brand).filter_by(id=brand_id).one()
    user_id = getUserID(login_session['email'])
    if user_id != editedItem.user_id:
        flash("you are not the creater of this mobile")
        return redirect(url_for('showMobile', brand_id=brand_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['image']:
            editedItem.image = request.form['image']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['rating']:
            editedItem.rating = request.form['rating']
        if request.form['offer']:
            editedItem.offer = request.form['offer']
        session.add(editedItem)
        session.commit()
        flash('Mobile Successfully Edited')
        return redirect(url_for('showMobile', brand_id=brand_id))
    else:
        return render_template(
            'editMobile.html',
            brand_id=brand_id,
            mobile_id=mobile_id,
            item=editedItem)


@app.route('/brand/<int:brand_id>/mobile/<int:mobile_id>/delete',
           methods=['GET', 'POST'])
def deleteMobile(brand_id, mobile_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Mobile).filter_by(id=mobile_id).one()
    brand = session.query(Brand).filter_by(id=brand_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Mobile Item Successfully Deleted')
        return redirect(url_for('showMobile', brand_id=brand_id))
    else:
        return render_template('deleteMobile.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
