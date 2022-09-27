import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash, session
from werkzeug.exceptions import abort
import logging

# session key to store db_connection_count per user session
db_connection_count_key = 'db_connection_count'

# Function to get a database connection.
# This function connects to database with the name `database.db`


def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    if db_connection_count_key in session:
        session[db_connection_count_key] += 1
    else:
        session[db_connection_count_key] = 1
    return connection

# Function to get a post using its ID


def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post

# Function to get the total number of posts in the DB


def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(ID) FROM posts').fetchone()
    connection.close()
    return post_count['COUNT(ID)']


# Define the Flask application
app = Flask(__name__)
app.secret_key = '39f012f89b483ff0b68d74123253a79f8caab4531b7e900f5d80606182b2ef6d'

# Define the main route of the web application


@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info(f'Article with id {post_id} does not exist')
        return render_template('404.html'), 404
    else:
        if post['title'] is not None:
            title = post['title']
            app.logger.info(f'Article "{title}" has been retrieved')
        return render_template('post.html', post=post)

# Define the About Us page


@app.route('/about')
def about():
    app.logger.info('Presenting information about us')
    app.logger.debug('Testing out debug logging')
    return render_template('about.html')

# Define the post creation functionality


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info(f'New article with title "{title}" created')
            return redirect(url_for('index'))

    return render_template('create.html')

# Define the healthcheck


@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Retrieving the health status')
    return response

# Define the metrics endpoint


@app.route('/metrics')
def metrics():
    db_connection_count = 0
    if db_connection_count_key in session:
        db_connection_count = session[db_connection_count_key]

    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": db_connection_count, "post_count": get_post_count()}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Retrieving the metrics information')
    return response


# start the application on port 3111
if __name__ == "__main__":

    # Set the default log level to DEBUG
    logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                        level=logging.DEBUG)

    app.run(host='0.0.0.0', port='3111')
