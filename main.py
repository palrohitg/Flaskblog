from flask import Flask, render_template, request, session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
import os
import math
from werkzeug import secure_filename

app = Flask(__name__)
app.secret_key = 'super-secret-key'


local_server = True
with open("config.json", "r") as c:
    params = json.load(c)["params"]

app.config['Upload_folder'] = params['file_uploader']
# Configure the mail use the SMTP gmail server
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-username'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

# config the database connectivity
if(local_server) :
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else :
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']

db = SQLAlchemy(app)

'''******************************************** MODEL OF THE DATABASE**********************************************************************'''
# Model of Contacts table
class Contacts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_no = db.Column(db.String(13), nullable=False)
    msg = db.Column(db.String(100), nullable=False)

# Model of Posts table
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(10), nullable=False)

'''********************************************************************************************************************************'''

'''********************************************* ROTUE OF THE HTTPS ****************************************************************'''
# yeh ab sikh ek jo python ka data template means ki index file par kaise send karte hai
@app.route('/')
def home() :
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    #slicing here
    posts = posts[(page-1)*int(params['no_of_posts']) :(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if(page == 1) :
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif(page == last) :
        prev = "/?page=" + str(page - 1)
        next = "#"
    else :
        prev =  "/?page=" + str(page - 1)
        next = "/?page="+ str(page + 1)
    return render_template("index.html", params=params, posts=posts, prev=prev, next=next)

@app.route('/about')
def about() :
    #name = "vikas"
    return render_template("about.html", params=params)

@app.route('/logout')
def logout() :
    session.pop('user')
    return redirect('/dashboard')


@app.route('/uploader', methods = ["GET", "POST"])
def uploader() :
    if ('user' in session and session['user'] ==  params['admin_username']) :
        if request.method == "POST" :
            f = request.files['file_uploader']
            f.save(os.path.join(app.config['Upload_folder'], secure_filename(f.filename)))
            return "successfully"
    return "woo"
#Admin Dashboard work here
@app.route('/dashboard', methods = ["GET", "POST"])
def dashboard() :

    if ('user' in session and session['user'] ==  params['admin_username']) :
        post = Posts.query.all()
        return render_template('dashboard.html', params=params, posts = post)

    if request.method == "POST" :
        uname = request.form['Username']
        password = request.form['pass']

        if (uname ==  params['admin_username']  and  password == params['admin_password'] ) :
            session['user'] = params['admin_username']
            post = Posts.query.all()

            return render_template("dashboard.html", params = params, posts=post)

    return render_template("login.html", params=params)

# Database varible name must be different to know which are the form varible and which are the db varible
# Don't make it same of the two  varible

@app.route('/contact', methods = ["GET", "POST"])
def contact() :
    
    if request.method == "POST" :
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        entry = Contacts(name=name, email=email, phone_no=phone, msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New message from" + name, 
                           sender=email, 
                           recipients=[params['gmail-username']],
                           body= message + "\n" + phone)
    return render_template("contact.html",params=params)



@app.route('/post/<string:post_slug>', methods = ['GET'])
def post_route(post_slug) :
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template("post.html",params=params, post = post)

@app.route('/Edit/<string:srno>', methods = ['GET', 'POST'])
def Edit(srno) :
    if ('user' in session and session['user'] ==  params['admin_username']) :
            if (request.method == "POST") :
                title_box = request.form['title']
                slug = request.form['slug']
                imgurl = request.form['img_url']
                contents = request.form['content']

                if srno == '0' :
                    post = Posts(title=title_box, slug=slug, content = contents,img_file=imgurl)
                    db.session.add(post)
                    db.session.commit()
                else :
                    post = Posts.query.filter_by(id=srno).first()
                    post.title = title_box
                    post.slug = slug
                    post.content = contents
                    post.img_file = imgurl
                    db.session.commit()
                    return redirect('/Edit/'+srno)
            post = Posts.query.filter_by(id=srno).first()
    return render_template("Edit.html", params=params, post=post, srno =srno)


    

app.run(debug=True)
