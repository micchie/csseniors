from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from csseniors import CSSeniors
from flask import Markup
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PAVouza4lX'
Bootstrap(app)

class NameForm(FlaskForm):
    name = StringField('First [M] Last', validators=[DataRequired()])
    submit = SubmitField('Go')

def pid2dblp(pid):
    return 'https://dblp.org/pid/{}.html'.format(pid)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    message = ""
    if form.validate_on_submit():
        formin = form.name.data
        mm = []
        if re.search('--', formin):
            formin = formin.replace('--', '')
            mm.append('--')
        name = re.split('[\+-]', formin)[0]
        args = [name]
        options = re.findall('[\+-].*?(?=[\+-]|$)', formin)
        options = [o.strip(' ') for o in options]
        cssenior = CSSeniors(args + options + mm)
        res = cssenior.getlog()
        res_html = ''
        for l in res:
            if not 'title' in l and not 'author' in l:
                ls = {k: v for k, v in sorted(l.items(),
                  key=lambda item:item[1]['latest'], reverse=True)}
                mm = ['<a href="{}">{}</a> <span style="font-size: 80%">(-{})'
                      '</span>'.format(pid2dblp(k[0]), k[1], v['latest'])
                        for k, v in ls.items()]
                res_html += '<p><div>Co-authors: {}</div></p>'.format(
                        ', '.join(mm))
            elif 'pid' in l:
                name = l['author']
                pid = l['pid']
                dblp = pid2dblp(pid)
                res_html += ('<h3>{} <span style="font-size: 14pt">(DBLP: '
                    '<a href="{}">{}</a>)</span></h3>'.format(name, dblp, pid))
            else:
                res_html += ('<div>{} <span style="font-weight: normal">'
                             '{} {} {}</span></div>'.format(l['title'],
                             ', '.join([a[1] for a in l['authors']]) + ', ',
                             l['conf'], l['year'])
                            )
        message = Markup(res_html)
    return render_template('index.html', form=form, message=message)

if __name__ == '__main__':
    app.run(debug=False)
