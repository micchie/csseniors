#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

# Copyright (C) 2020 Michio Honda.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
#Falsemodification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the project nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE PROJECT AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE PROJECT OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import sys
import re
import urllib.request as urlreq
import requests

class Paper(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data.get(name) if name in self.data else None

class CSSenior(object):
    def __init__(self, name):
        self.msgs = []
        self.confs = self.parse_csrankings()
        self.tweak_confs(self.confs)

        #
        # Author list that matches the name
        #
        query_base = 'https://dblp.org/search/'
        query_author = 'author/api?q={}&format=json'.format(
                '%20'.join(name.split()))
        res = requests.get(query_base + query_author)
        res = res.json()['result']
        authors = []
        for h in res['hits']['hit']:
            author = [h['info']['author']]
            if 'aliases' in h['info']:
                author.append(h['info']['aliases']['alias'])
            authors.append((author,
                '/'.join(h['info']['url'].split('/')[-2:])))

        #
        # Paper list that includes the name
        #
        query_publ = 'publ/api?q={}&format=json&h=1500'.format(
                '%20'.join(name.split()))
        res = requests.get(query_base + query_publ)
        res = res.json()['result']

        papers = []
        for h in res['hits']['hit']:
            paper = Paper(h['info'])
            papers.append(paper)

        #
        # Count for each matching author
        #
        for author, pid in authors:
            self.log(('\n### ', name, pid))
            count = False
            tmp = []
            for paper in reversed(papers):
                if not isinstance(paper.authors['author'], list):
                    paper.authors['author'] = [paper.authors['author']]
                pids = [a['@pid'] for a in paper.authors['author']]
                if pid not in pids:
                    continue
                authors = [a['text'] for a in paper.authors['author']]
                paper.author_list = authors
                conf = ''
                conf = paper.key.split('/')
                if len(conf) != 3:
                    continue
                conf = conf[1].lower()
                if not conf in self.confs:
                    continue
                if not self.full_paper(conf, paper.title, paper.venue,
                        paper.pages, paper.year, paper.key):
                    continue
                d = {'title': paper.title, 'authors': paper.author_list,
                        'conf': conf.upper(), 'year': paper.year}
                if not count:
                    if paper.author_list[0] not in author:
                        tmp.append(d)
                        continue
                    count = True
                    for p in tmp:
                        if int(paper.year) - int(p['year']) <= 1:
                            self.log(p.values())
                    tmp = []
                self.log(d.values())

    def log(self, msg):
        self.msgs.append(msg)

    def getlog(self):
        return self.msgs

    @staticmethod
    def parse_csrankings():
        confs = []
        confline = 'https://dblp.org/db/conf/'
        page = urlreq.urlopen('http://csrankings.org')
        nodef = False
        comment = False
        pat_comment_on = re.compile('\s+<!--')
        pat_comment_off = re.compile('-->')
        pat_on = re.compile('\s+<td colspan="2">')
        pat_off = re.compile('\s+</table>')

        for l in page.readlines():
            s = l.decode()
            if pat_comment_on.search(s):
                if pat_comment_off.search(s):
                    comment = False
                    continue
                comment = True
            if pat_comment_off.search(s):
                comment = False
                continue
            if comment:
                continue

            if pat_on.search(s):
                nodef = True
            if nodef and pat_off.search(s):
                nodef = False
            if re.search(confline, s):
                if not nodef:
                    confs.append( s.split(confline)[1].split('/')[0] )
        return confs

    @staticmethod
    def tweak_confs(l):
        l.extend(['iclr', 'ndss', 'cvpr', 'pvldb'])
        #for c in ['emsoft', 'rtas', 'rtss', 'iccad', 'dac']:
        #    l.remove(c)

    @staticmethod
    def full_paper(conf, title, booktitle, pages, year, key):
        try:
            year = int(year)
            start, end = pages.split('-')
        except:
            return False
        if start.isdigit() and end.isdigit():
            numpages = int(end) - int(start) + 1
        else:
            return False
        if numpages < 8:
            return False
        for p in ['Poster', 'Demo', 'Experience']:
            if re.match(p, title):
                return False
        # workshop?
        if re.search('@', booktitle):
            return False
        # filter out AsiaCCS
        if conf == 'imc' or conf == 'sigcomm':
            if numpages < 10:
                # SIGCOMM 2002-2004 have position papers
                return False
        elif conf == 'ccs':
            for k in ('Asia', 'CCSW'):
                if re.search(k, booktitle):
                    return False
        elif conf == 'mobicom':
            if re.search('WSNA', booktitle):
                return False
        elif conf == 'huc':
            if numpages < 10:
                return False
            if re.search('Adjunct', booktitle):
                return False
        elif conf == 'micro':
            if re.search('IEEE', booktitle):
                return False
        elif conf == 'www':
            if key.split('/')[0] == 'journals':
                return False

        elif conf == 'kdd':
            if year == 2018:
                if int(start) >= 5 and int(end) < 1089:
                    return False
            elif year == 2019:
                if int(start) >= 1743:
                    return False
            elif year == 2020:
                if int(start) >= 2247:
                    return False
        elif conf == 'nsdi':
            if year == 2014 or year == 2015:
                res = requests.get('https://www.usenix.org/conference/'
                        'nsdi{}/technical-sessions'.format(str(year)[2:]))
                op = False
                for l in res.text.split('\n'):
                    if re.search('technical-sessions/session/'
                                 'operational-systems-track', l):
                        op = True
                    elif re.search('technical-sessions/session/', l):
                        op = False
                    if not op:
                        continue
                    if re.search('<h2 class="node-title clearfix">'
                            '<a href="/conference/nsdi{}/technical-sessions/'
                            'presentation/'.format(str(year)[2:]), l):
                        m = re.compile('<.*?>')
                        t1 = title
                        t2 = m.sub('', l, count=9)

                        m = re.compile('^\s+')
                        t1 = m.sub('', t1)
                        t2 = m.sub('', t2)
                        m = re.compile('\.$')
                        t1 = m.sub('', t1)
                        t2 = m.sub('', t2)
                        m = re.compile('(-|:)')
                        t1 = m.sub(' ', t1)
                        t2 = m.sub(' ', t2)
                        m = re.compile('\s+')
                        t1 = m.sub(' ', t1)
                        t2 = m.sub(' ', t2)
                        if t1.lower() == t2.lower():
                            return False
        return True

if __name__ == '__main__':
    css = CSSenior(sys.argv[1])
    for l in css.getlog():
        print(*l)
