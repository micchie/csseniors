from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from cssenior.cssenior import CSSenior
from flask import Markup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PAVouza4lX'
Bootstrap(app)

readme = """
"""

class NameForm(FlaskForm):
    name = StringField('First [M] Last', validators=[DataRequired()])
    submit = SubmitField('Go')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    message = ""
    if form.validate_on_submit():
        name = form.name.data
        cssenior = CSSenior(name)
        res = cssenior.getlog()
        res_html = ''
        for l in res:
            if 'author' in l:
                res_html += '<h2>{}</h2>'.format(l['author'])
            else:
                res_html += '<div>{}</div>'.format(l['paper'])
        message = Markup(res_html)
    return render_template('index.html', form=form, message=message)

if __name__ == '__main__':
    app.run(debug=True)
