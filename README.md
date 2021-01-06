# CSSeniors

```
python3 csseniors.py "First [M] Last" [+conf] [-conf] [--] [+c] 
```
This script shows the papers of a given author that have been published at the venues listed in
[CSRankings](http://csrankings.org) (plus ICLR) since their
first first-author paper.
The rational of such a list is that the first authorship of a top-tier
conference paper should indicate the work is
driven and built by their own, which proves the experience to deserve some
seniority.
Since a paper can be published later than others because of rejections,
this app also considers papers published in the
previous year of the first-author paper.
Webapp is also available at
[http://www.csseniors.org](http://www.csseniors.org).

### Options

You can add/remove conferences using +/- followed by a conference
key (uai if the DBLP entry is
https://dblp.org/db/conf/uai), like "John Smith +aistats +uai -aaai".

You can also remove all the conferences not selected by default in CSRankings using "--" option, which is overwritten by + options.

When "+c" option is given, this app also lists senior co-authors (this
process takes a bit long), which could be useful to guess the
collaboration circle of the author.

### Note

This app makes the best effort for accuracy, such as filtering out
short/workshop papers, applied data science track papers in KDD
(2018-2020), operational systems track papers in NSDI (2014-2016) and
experience papers in MOBICOM.

For any suggestion or bug report, please create a [Github
issue](https://github.com/micchie/csseniors/issues).
