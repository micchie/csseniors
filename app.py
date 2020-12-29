from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from cssenior import CSSenior

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PAVouza4lX'
Bootstrap(app)

class NameForm(FlaskForm):
    name = StringField('First [M] Last', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    readme = 'CSSenior'
    form = NameForm()
    message = ""
    if form.validate_on_submit():
        name = form.name.data
        cssenior = CSSenior(name)
        message = cssenior.getlog()
    return render_template('index.html', form=form, message=message, readme=readme)

if __name__ == '__main__':
    app.run(debug=True)
