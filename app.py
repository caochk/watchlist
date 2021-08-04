from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

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
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))  # 用于存放用户密码对应散列值

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # 生成后直接存入类的属性中

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


# 清空数据库并重新创建注册为命令
@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
# 设置选项
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


# 将虚拟数据插入数据库表，并注册为命令
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


# 将生成管理员账户注册为命令
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    db.create_all()  # 建表：因为之前修改了user类，里面加入了两个新的属性。所以生成了数据库。但是感觉此处的建表之前已经做了（不理解）？？？
    # 这个建表，好像如果之前表已经在了，就不会覆盖地建，而是就跳过了。没有的话才会建
    user = User.query.first()
    if user:  # 管理员用户已存在，那就进行更新操作
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:  # 管理员不存在即创建
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()  # 若是更新数据，无需add，直接提交即可
    click.echo('Done.')


login_manager = LoginManager(app)  # 实例化扩展类
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户ID作为参数
    user = User.query.get(int(user_id))  # 用ID作为User模型的主键查询对应的用户
    return user  # 返回用户对象


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 先验证用户名、密码是否输入
        if not username or not password:
            flash('Invalid input!')
            return redirect(url_for('login'))  # 输入有误后，直接重定向到依然是login界面，接着重新输入

        # 通过了验证是否输入，现在还需验证用户名和该用户名对应密码是否匹配
        user = User.query.first()
        if username == user.username and user.check_password(password):
            login_user(user)  # 都通过了就登入
            flash('Login success.')
            return redirect(url_for('index'))  # 登入完重定向回主页
        else:  # 如果验证失败
            flash('Login failed.')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()  # 登出用户
    flash('See you!')
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    # 分别处理post请求与get请求
    if request.method == 'POST':
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 就重定向回到主页
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
@login_required  # 只有登录后才可用此视图函数
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
@login_required
def delete(movie_id):
    # 先行验证：看看传进来的movie_id在数据库里有没有，该方法若没找到会直接返回404响应
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted !')
    return redirect(url_for('index'))  # 视图函数好像必须有返回


# 设置界面允许用户修改用户名
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        name = request.form.get('name')
        # 先验证有无输入新名字，或者新名字长度是否可行
        if not name or len(name) > 20:
            flash('Invalid input')
            return redirect(url_for('settings'))
        # 验证通过
        current_user.name = name  # 等价于user=User.query.first() + user.name=name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    else:
        return render_template('settings.html')


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
