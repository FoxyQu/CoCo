from flask import Flask, render_template, request
from create_db import db
from functions import total_search

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data_pis_ko.db'

db.app = app
db.init_app(app)

'''@app.before_request
def create_tables():
    # The following line will remove this handler, making it
    # only run on the first request
    app.before_request_funcs[None].remove(create_tables)

    db.create_all()'''

@app.route('/', methods=['GET'])
def main():
    return render_template('index.html')

@app.route('/res', methods=['GET'])
def user_search():
    query = dict(request.args)['q']
    data = total_search(query)
    #data.append(len(data))
    return render_template('index.html', data=data, res='Результат запроса:', q=query)

if __name__ == '__main__':
    app.run(debug=True)
