
import os
import redis
from flask import Flask, render_template, request, redirect, url_for

# Initialize Flask app and Redis connection
app = Flask(__name__)
redis_host = os.getenv('REDIS_HOST', 'redis')  # Use the hostname from the docker-compose file
redis_client = redis.Redis(host=redis_host, port=6379)

# Function to maintain hit count
def get_hit_count():
    retries = 5
    while True:
        try:
            return redis_client.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1

# Home page with hit count
@app.route('/')
def index():
    count = get_hit_count()
    return f'Hello! You have visited this page {count} times.'

# Route to show form for adding name and email
@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        # Store the name and email in Redis (use name as the key for sorting)
        redis_client.hset(name, 'email', email)
        
        return redirect(url_for('list_users'))
    
    return '''
        <form method="post">
            Name: <input type="text" name="name"><br>
            Email: <input type="email" name="email"><br>
            <input type="submit" value="Add User">
        </form>
    '''

# Route to display sorted list of users by name
@app.route('/users')
def list_users():
    # Get all users (names) from Redis and sort them
    keys = redis_client.keys('*')
    users =[]
    for key in keys:
        #make sure key is a hash
        if redis_client.type(key) == b'hash':
            name = key.decode()
            email = redis_client.hget(key, 'email').decode()
            users.append((name, email))

    # Display users in a sorted list
    users.sort()
    user_list = '<ul>'
    for name, email in users:
        user_list += f'<li>{name}: {email}</li>'
    user_list += '</ul>'
    
    return f'''
        <h2>List of Users (Sorted by Name)</h2>
        {user_list}
        <a href="/add">Add another user</a>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
