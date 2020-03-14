import os
import sys
import click

from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask import flash

prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path,'data.db')  #写入一个SQLALCHEMY_DATABASE_URI变量来告诉SQLAILchemy数据库连接地址
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    #关闭对模型修改的监控
db = SQLAlchemy(app)  #初始化扩展，传入程序实例 app

class User(db.Model):   #表名将会是user;模型类要声明db.Model;每一个类属性要实例化db.Column，传入的参数为字段的类型。
    id = db.Column(db.Integer, primary_key=True)   #主键
    name = db.Column(db.String(20))     #名字

class Movie(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

#对于多个模板都需要使用的函数，可以使用app.context_processor装饰器注册一个模板上下文处理函数
#该函数返回的变量(以字典键值对的形式)将会统一注入到每一个模板的上下文
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)  #需要返回字典，等同于return {'user':user}

@app.cli.command()
def forge():
    """"Generate fake date."""
    db.create_all()

    #全局的两个变量移动到这个函数内
    name = 'Jesse'
    movies = [
        {'title': 'My Neighbor Totoro', 'year':'1988'},
        {'title': 'Dead Poets Society', 'year':'1989'},
        {'title': 'A Perfect World', 'year':'1993'},
        {'title': 'Leon', 'year':'1994'},
        {'title': 'Mahjong', 'year':'1996'},
        {'title': 'Swallowtail Butterfly', 'year':'1996'},
        {'title': 'King of Comedy', 'year':'1999'},
        {'title': 'Devils on the Doorstep', 'year':'1999'},
        {'title': 'WALL-E', 'year':'2008'},
        {'title': 'The Pork of Music', 'year':'2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'],year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')



@app.route('/', methods=['GET', 'POST']) #在app.route()装饰器里，可以用methods关键字传递一个包含HTTP方法字符串的列表，
def index():                            #表示这个视图函数处理哪种方法类型的请求
    if request.method == 'POST':    #判断是否是post请求
        #获取表单数据,request.form是一个特殊字典，用表单字段的name属性可以获取用户填入的对应数据
        title = request.form.get('title')   #传入表单对应输入字段的name值
        year = request.form.get('year')
        #验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') #显示错误提示
            return redirect(url_for('index'))      #重定向回主页
        #保存表单数据到数据库
        movie = Movie(title=title, year=year)   #创建记录
        db.session.add(movie)   #添加到数据库会话
        db.session.commit   #提交数据库会话
        flash('Item created.')  #显示创建成功的提示,flash()函数用来在是凸函数里向模板传递提示消息
        return redirected(url_for('index'))
    user = User.query.first()
    movies = Movie.query.all()  #读取所有的电影记录
    return render_template('index.html',user=user,movies=movies)

@app.cli.command()  #注册为命令
#使用click提供的option装饰器为命令添加一个 --drop选项，将is_flag参数设置为True,就可以将这个选项声明为布尔值标志，
# --drop选项的值作为drop参数传入命令函数
#如果提供了这个选项，drop的值就为Ture，清空数据库的内容
@click.option('--drop',is_flag=True,help='Create after drop.')  #设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.') #输出提示信息

#使用app.errorhandler()装饰器注册一个错误处理函数，当404错误发生时，函数被触发，返回值会作为响应主体返回给客户端
@app.errorhandler(404)  #传入要处理的错误代码
def page_not_found(e):  #接受异常对象作为参数
    return render_template('404.html'),404    #返回模板和状态码

#编辑电影条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET','POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':    #处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) > 4 or len(title) >60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  #重定向回对应的编辑页面

        movie.title = title #更新标题
        movie.year = year   #更新年份
        db.session.commit() #提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))   #重定向回主页

    return render_template('edit.html',movie=movie) #c传入被编辑的电影记录
app.config['SECRET_KEY'] = 'dev'

#删除电影条目
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])    #限定只接受post请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)    #获取电影记录
    db.session.delete(movie)    #删除对应的记录
    db.session.commit() #提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))



# @app.route('/')
# def hello():
#     return '<h1>Hello,Flask</h1><img src="http://helloflask.com/totoro.gif">'

# from flask import Flask
# from flask import escape
# app = Flask(__name__)
#
# @app.route('/user/<name>')
# def user_page(name):
#     return 'User: %s' % escape(name)



# from flask import url_for,escape
# from flask import Flask
# app = Flask(__name__)
#
# @app.route('/')
# def hello():
#     return 'Hello,World'
#
# @app.route('/user/<name>')
# def user_page(name):
#     return 'User: %s' % escape(name)
#
# @app.route('/test')
# def test_url_for():
#     print(url_for('Hello'))
#     print(url_for('user_page',name='Jesse'))
#     print(url_for('user_page',name='Wu'))
#     print(url_for('test_url_for'))
#     print(url_for('test_url_for',num=2))
#     return 'Test page'