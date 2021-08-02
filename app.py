from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click

app = Flask(__name__)
app.secret_key = 'wndwuibfw'  # 消息闪现需要对内容进行加密，所以需要密钥做加密消息的混淆

# 数据库准备工作
WIN = sys.platform.startswith('win')
if WIN:  # 若为Windows系统，配置变量中关于数据库路径须如此开头
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(app)  # 在扩展类实例化之前加载写好的配置

# 创建数据库模板类
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

@app.cli.command()
def forge():
    '''自定义命令：生成虚拟数据'''
    db.create_all()  # 创建数据库

    name = 'Jason Cao'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead	Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King	of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)  # 将新创建的记录添加到数据库会话
    db.session.commit()  # 提交记录
    click.echo('Done!')  # 输出一个信息


@app.route('/', methods=['GET', 'POST'])
def index():
    # 分别处理post请求与get请求
    if request.method == 'POST':
        # post请求用于获取用户提交的电影与年份信息，将其存入数据库
        title = request.form.get('title')  # 靠表单中的name值来进行对应
        year = request.form.get('year')
        # 判断用户输入的信息是否有误
        if len(title) > 60 or len(year) != 4 or not year or not title:
            flash('Invalid input !')  # 靠消息闪现来提醒用户
        # 无误就存入数据库
        else:
            movie = Movie(title=title, year=year)  # 创建movie记录
            db.session.add(movie)  # 记录加到数据库会话
            db.session.commit()  # 提交记录
            flash('Item created !')
        return redirect(url_for('index'))  # 重定向会主页（即根地址）

    # 不是post命令就是get命令，get就直接返回主页
    # user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


# 以下视图函数处理用户输入的待更新数据
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    # 先行验证：看看传进来的movie_id在数据库里有没有，该方法若没找到会直接返回404响应
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')
        # 先验证输入是否有误
        if not title or not year or len(title) > 60 or len(year) != 4:
            flash('Invalid input !')
        else:
            movie.title = title
            movie.year = year
            db.session.commit()  # 更新完直接提交
            flash('Item updated !')
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('edit.html', movie=movie)  # 数据流转：点击edit按钮，会重定向到edit端口，
        # 那么就需要该视图函数来进行处理。然后视图函数先拿着传进来的movie_id去数据库里找有无此项，找到了就先应答get请求，把movie数据
        # 先传入edit模板。因为edit模板的表单里用了value属性，等着这个值直接填上去呢！
        # 然后用户点击update按钮发起post请求。再是到该视图函数的post处理部分了。


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
    # 先行验证：看看传进来的movie_id在数据库里有没有，该方法若没找到会直接返回404响应
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted !')
    return redirect(url_for('index'))  # 视图函数好像必须有返回

# 模板上下文处理函数：以下一处函数中返回的变量可用于所有用到该变量的模板（其他视图函数里涉及获取此变量的函数代码全部可以省略了）
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)  # 必须返回字典形式


@app.errorhandler(404)
def page_not_found(e):
    # user = User.query.first()
    return render_template('404.html'), 404  # 返回404模板和状态码

if __name__ == '__main__':
    app.run(debug=True)
