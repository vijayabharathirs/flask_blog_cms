import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set the secret key to be read from an environment variable
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')  # Use 'default_secret_key' if not set

# MongoDB connection using your connection string
client = MongoClient('mongodb+srv://arthisrini26:frzoCrcRWwTUaoWv@cluster0.chjio.mongodb.net/myBlogDB?retryWrites=true&w=majority')
db = client['myBlogDB']  # Specify the database name
posts_collection = db['posts']  # Specify the posts collection name
users_collection = db['users']  # Specify the users collection name

# Configure upload folder for images
UPLOAD_FOLDER = 'uploads'  # Specify your upload folder path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route - shows all blog posts
@app.route('/')
def index():
    posts = posts_collection.find()
    return render_template('index.html', posts=posts)

# Create new post
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required!', 'error')
            return redirect(url_for('create'))

        post = {'title': title, 'content': content}
        posts_collection.insert_one(post)
        flash('Post created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create.html')

# Edit post
@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        flash('Post not found!', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_url = post.get('image_url')  # Default to current image URL

        if not title or not content:
            flash('Title and content are required!', 'error')
            return redirect(url_for('edit', post_id=post_id))

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:  # Check if a file is uploaded
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)  # Sanitize the file name
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)  # Save the file
                    image_url = url_for('uploaded_file', filename=filename)  # Create the URL
                else:
                    flash('Invalid image file format!', 'error')
                    return redirect(url_for('edit', post_id=post_id))

        # Update the post in your database
        posts_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'title': title, 'content': content, 'image_url': image_url}}
        )
        flash('Post updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', post=post)

# Function to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Delete post
@app.route('/delete/<post_id>')
def delete(post_id):
    posts_collection.delete_one({'_id': ObjectId(post_id)})
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('index'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not password or not confirm_password:
            flash('All fields are required!', 'error')
            return redirect(url_for('signup'))
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))

        # Hash the password and create the user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = {'email': email, 'password': hashed_password}
        users_collection.insert_one(user)
        
        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))  # Redirect to the login page after signup

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user exists
        user = users_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            # Successful login
            session['user_id'] = str(user['_id'])  # Store the user's ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            # Invalid credentials
            flash('Invalid email or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user ID from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
