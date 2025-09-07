from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key'  # Flashメッセージ用の秘密鍵を設定

db = SQLAlchemy(app)
migrate = Migrate(app, db)

#Reviewモデルの更新
class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    review = db.Column(db.String(300), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  
    course = db.relationship('Course', backref=db.backref('reviews', lazy=True))

#Courseモデルの更新
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    star_rating = db.Column(db.Float, default=0.0)  

with app.app_context():
    db.create_all()
    
@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('top.html', courses=courses)

@app.route('/add', methods=['POST'])
def add_course():
    course_name = request.form['name']
    course_teacher = request.form['teacher']

    #同じ講義名と先生の名前の講義が既に存在するかをチェック
    existing_course = Course.query.filter_by(name=course_name, teacher=course_teacher).first()
    if existing_course:
        flash('同じ授業がすでに登録されています。', 'course_error')
        return redirect(url_for('index'))

    new_course = Course(name=course_name, teacher=course_teacher)
    db.session.add(new_course)
    db.session.commit()
    return redirect(url_for('course_detail', id=new_course.id))

@app.route('/delete/<int:id>', methods=['GET'])
def delete_course(id):
    course_to_delete = Course.query.get_or_404(id)
    db.session.delete(course_to_delete)
    db.session.commit()
    return redirect('/manage')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search']
        results = Course.query.filter(
            (Course.name.like(f'%{search_term}%')) | (Course.teacher.like(f'%{search_term}%'))
        ).all()
        return render_template('search.html', results=results)
    return render_template('search.html', results=[])

@app.route('/manage')
def manage():
    courses = Course.query.all()
    return render_template('manage.html', results=courses)

@app.route('/course/<int:id>')
def course_detail(id):
    course = Course.query.get_or_404(id)
    return render_template('detail.html', course=course, reviews=course.reviews)

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form['password']
    if password == 'password':
        return redirect(url_for('manage'))
    else:
        flash('パスワードが間違っています。', 'admin_error')
        return redirect(url_for('index'))


import math
@app.route('/add_review/update/<int:id>', methods=['POST'])
def update_course_rating(course_id):
    course = Course.query.get(course_id)
    if course:
        #講義のレビューを取得
        reviews = Review.query.filter_by(course_id=course_id).all()
        if reviews:
            #レビューのレーティングをリストとして取得
            ratings = [review.rating for review in reviews]
            #平均を計算
            average_rating = math.floor((sum(ratings) / len(ratings)) * 100) / 100
            #コースのstar_ratingを更新
            course.star_rating = average_rating
            db.session.commit()

@app.route('/add_review/<int:id>', methods=['POST'])      
def add_review(id):
    course_review = request.form['review']
    rating = int(request.form['rating'])  #レーティングを取得
    new_review = Review(course_id=id, review=course_review, rating=rating)
    db.session.add(new_review)
    db.session.commit()
    update_course_rating(id)  #コースの平均レーティングを更新
    return redirect(url_for('course_detail', id=id))

@app.route('/delete_review/<int:id>', methods=['POST', 'GET'])
def delete_review(id):
    review_to_delete = Review.query.get_or_404(id)
    db.session.delete(review_to_delete)
    db.session.commit()
    return redirect(url_for('course_detail_admin', id=review_to_delete.course_id))

@app.route('/course_admin/<int:id>')
def course_detail_admin(id):
    course = Course.query.get_or_404(id)
    return render_template('detail2.html', course=course, reviews=course.reviews)

if __name__ == "__main__":
    app.run(debug=True)
