from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click

app = Flask(__name__)

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

@app.route('/')
def index():
    # user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

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
