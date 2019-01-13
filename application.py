from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from database_setup import Base, Category, Item, User
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from flask import make_response

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "caltalog app"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db?check_same_thread=false')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
        response = make_response(json.dumps("""
        Token's client ID does not match app's."""), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("""
        Current user is already connected."""), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ ' style = "width: 300px;
    height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;'> """
    flash("""you are now
     logged in as %s""" % login_session['username'])
    print "done!"
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
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps("""
        Failed to revoke token for given user.""", 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show categories and latest items
@app.route('/')
@app.route('/catalog')
def catalog():
    categories = session.query(Category).order_by(asc(Category.title))
    items = session.query(Item).order_by(desc(Item.id))
    if 'username' not in login_session:
        return render_template('public_catalog.html',
                               categories=categories, items=items)
    else:
        return render_template('catalog.html',
                               categories=categories, items=items)


# show a category items
@app.route('/catalog/<string:category_title>')
@app.route('/catalog/<string:category_title>/items')
def browse_category_items(category_title):
    categories = session.query(Category).order_by(asc(Category.title))
    selected_category = session.query(Category).filter_by(
        title=category_title).one()
    items = session.query(Item).filter_by(
        category_id=selected_category.id).all()
    return render_template(
        'category_items.html', categories=categories,
        selected_category=selected_category, items=items)


@app.route('/catalog/<string:category_title>/<string:item_title>')
def browse_item(category_title, item_title):
    selected_category = session.query(Category).filter_by(
        title=category_title).one()
    item = session.query(Item).filter_by(
        category_id=selected_category.id, title=item_title).one()
    if 'username' not in login_session:
        return render_template('public_item.html', item=item)
    else:
        return render_template('item.html', item=item)


# edit an item
@app.route('/catalog/<string:item_title>/edit', methods=['GET', 'POST'])
def edit_item(item_title):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(title=item_title).one()
    categories = session.query(Category).order_by(asc(Category.title))
    if login_session['user_id'] != editedItem.user_id:
        return """<script>function myFunction(){
            alert('You are not authorized to edit this item.\
            Please create your own item in order to edit it.');
            }
        </script>
        <body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('catalog'))
    else:
        return render_template(
            'edit_item.html', categories=categories, item=editedItem)


# delete an itme
@app.route('/catalog/<string:item_title>/delete', methods=['GET', 'POST'])
def delete_item(item_title):
    itemToDelete = session.query(Item).filter_by(title=item_title).one()
    if 'username' not in login_session:
        return redirect('/login')
    if itemToDelete.user_id != login_session['user_id']:
        return """<script>
        function myFunction(){
            alert('You are not authorized to delete this restaurant.\
            Please create your own restaurant in order to delete.');
            }
         </script>
         <body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('%s Successfully Deleted' % itemToDelete.title)
        session.commit()
        return redirect(url_for('catalog'))
    else:
        return render_template('delete_item.html', item=itemToDelete)


# create a  new item
@app.route('/catalog/add_item', methods=['GET', 'POST'])
def add_item():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.title))
    if request.method == 'POST':
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.title))
        return redirect(url_for('catalog'))
    else:
        return render_template('add_item.html', categories=categories)


# Disconnect
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('catalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('catalog'))


# JSON APIs to view catalog Information
@app.route('/catalog/<string:category_title>/JSON')
@app.route('/catalog/<string:category_title>/items/JSON')
def browse_category_items_JSON(category_title):
    category = session.query(Category).filter_by(title=category_title).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<string:category_title>/<string:item_title>/JSON')
def ItemJSON(category_title, item_title):
    ItemJSON = session.query(Item).filter_by(title=item_title).one()
    return jsonify(ItemJSON=ItemJSON.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
