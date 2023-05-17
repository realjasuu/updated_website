from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from .models import Post, Upload, User, Comment, Like
from . import db
import os
from werkzeug.utils import secure_filename
from .models import Post
from io import BytesIO





views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template("home.html", user=current_user, posts=posts)



UPLOAD_FOLDER = r'static\img\uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@views.route('/create-post/<post_id>', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']

        upload = Upload(filename=file.filename, data=file.read())
        db.session.add(upload)
        db.session.commit()

        return f'Uploaded: {file.filename}'
    return render_template('index.html', user=current_user)

@views.route('/download/<upload_id>', methods=['POST'])
def download(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(BytesIO(upload.data), attachment_filename=upload.filename, as_attachment=True)

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        image = request.form.get('image')
        text = request.form.get('text')
        attachment = request.files.get('attachment')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()

            if attachment:
                filename = secure_filename(attachment.filename)
                if filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                    # Create the uploads directory if it doesn't exist
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    attachment.save(filepath)
                    flash(f"Attachment: {filepath}", category="success")
                else:
                    flash('Invalid attachment file type', category='error')

            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)


@views.route("/delete-post/<int:id>")
@login_required
def delete_post(id):
    post = Post.query.get(id)

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.user.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))

@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)

@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))

@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have a permission to delete this comment', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()
    return redirect(url_for('views.home'))

@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exists.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})