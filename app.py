from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'


if __name__ == '__main__':
    app.run(debug=True)
