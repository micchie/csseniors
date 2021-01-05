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

class CSSeniors(object):
    def __init__(self, args, uid=None, frst=False, confs=None, nsdiprogs={}):
        countca = False
        self.msgs = []
        self.nsdiprogs = nsdiprogs
        if confs:
            self.confs = confs
        else:
            self.confs, self.nodef_confs = CSSeniors.parse_csrankings()
            CSSeniors.tweak_confs(self.confs)
            self.confs |= self.nodef_confs
        add_confs = set() # overwrite '--' option
        for a in args:
            if re.match('\+c$', a):
                countca = True
            elif re.match('\+\S\S+', a):
                add_confs.add(a.lstrip('+'))
            elif re.match('--$', a):
                self.confs ^= self.nodef_confs
            elif re.match('-\S\S+', a):
                noconf = a.lstrip('-')
                if noconf in self.confs:
                    self.confs.remove(noconf)
            else:
                name = a
        self.confs |= add_confs

        #
        # Author list that matches the name
        #
        query_base = 'https://dblp.org/search/'
        query_author = 'author/api?q={}&format=json'.format(
                '%20'.join(name.split()))
        res = requests.get(query_base + query_author)
        if not 'result' in res.json():
            return
        res = res.json()['result']
        authors = []
        if not 'hits' in res:
            return
        if not 'hit' in res['hits']:
            return

        for h in res['hits']['hit']:
            author = [h['info']['author']]
            url = url = '/'.join(h['info']['url'].split('/')[-2:])
            if uid:
                if uid != url:
                    continue
            if 'aliases' in h['info']:
                author.append(h['info']['aliases']['alias'])
            authors.append((url, author))
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
        for pid, author in authors:
            self.log({'author': name, 'pid': pid})
            count = False
            tmp = []
            coauthors = {}
            for paper in reversed(papers):
                if not isinstance(paper.authors['author'], list):
                    paper.authors['author'] = [paper.authors['author']]
                paper.authors2 = [(a['@pid'], a['text'])
                        for a in paper.authors['author']]
                if pid not in [a[0] for a in paper.authors2]:
                    continue
                conf = paper.key.split('/')
                if len(conf) != 3:
                    continue
                conf = conf[1].lower()
                if not conf in self.confs:
                    continue
                if not self.full_paper(conf, paper.title, paper.venue,
                        paper.pages, paper.year, paper.key):
                    continue

                d = {'title': paper.title, 'authors': paper.authors2,
                        'conf': conf.upper(), 'year': paper.year}
                if not count:
                    if paper.authors2[0][0] != pid:
                        tmp.append(d)
                        continue
                    count = True
                    for p in tmp:
                        if int(paper.year) - int(p['year']) <= 1:
                            for a in p['authors']:
                                if a[0] != pid and countca:
                                    CSSeniors.add_coauthor(coauthors, a,
                                            int(p['year']))
                            self.log(p)
                for a in paper.authors2:
                    if a[0] != pid and countca:
                        CSSeniors.add_coauthor(coauthors, a, int(paper.year))
                self.log(d)
                if frst:
                    break
            #
            # Filter out junior coauthors
            #
            if countca:
                seniors = []
                for ca in coauthors:
                    args2 = []
                    for a in [ca[1], *args]:
                        if not re.match('\+c$', a) and a != name:
                            args2.append(a)
                    css = CSSeniors(args2, uid=ca[0], frst=True,
                            confs=self.confs, nsdiprogs=self.nsdiprogs)
                    for m in css.getlog():
                        if 'title' in m:
                            seniors.append(ca)
                            break
                coauthors = {k: v for k, v in coauthors.items() if k in seniors}
                self.log(coauthors)

    def log(self, msg):
        self.msgs.append(msg)

    def getlog(self):
        return self.msgs

    @staticmethod
    def add_coauthor(coauthors, a, y):
        if a in coauthors:
            coauthors[a]['#'] += 1
            if y > coauthors[a]['latest']:
                coauthors[a]['latest'] = y
        else:
            coauthors[a] = {}
            coauthors[a]['#'] = 1
            coauthors[a]['latest'] = y

    @staticmethod
    def parse_csrankings():
        confs = set()
        nodef_confs = set()
        confline = 'https://dblp.org/db/conf/'
        page = urlreq.urlopen('http://csrankings.org')
        nodef = False
        comment = False
        pat_comment_on = re.compile('\s+<!--')
        pat_comment_off = re.compile('-->')
        pat_on = re.compile('\s+<td colspan="2">')
        pat_off = re.compile('\s+</table>')
        area_sep = re.compile('<span class="hovertip" id=')
        reset_area = False
        next_area_sep = re.compile('</span>')
        next_area = False
        next_area_skip = re.compile('<label for="')
        cur_area = ''

        strps = [(re.compile('\s+$'), ''),
                (re.compile('^\s+'), ''),
                (re.compile('&nbsp;'), ''),
                (re.compile('&amp;'), '&')]

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

            if next_area:
                if next_area_skip.search(s):
                    continue
                for strp in strps:
                    s = strp[0].sub(strp[1], s)
                cur_area = s
                reset_area = False
                next_area = False
            elif area_sep.search(s):
                reset_area = True
            elif reset_area:
                if next_area_sep.search(s) or next_area_skip.search(s):
                    next_area = True

            if pat_on.search(s):
                nodef = True
            if nodef and pat_off.search(s):
                nodef = False
            if re.search(confline, s):
                if not nodef:
                    confs.add( s.split(confline)[1].split('/')[0] )
                else:
                    nodef_confs.add( s.split(confline)[1].split('/')[0] )
        return confs, nodef_confs

    @staticmethod
    def tweak_confs(confs):
        for c in ['iclr', 'ndss', 'cvpr', 'pvldb']:
            confs.add(c)
        #for c in ['emsoft', 'rtas', 'rtss']:
        #    confs.remove(c)

    @staticmethod
    def norm_title(title, line):
        m = re.compile('<.*?>')
        t1 = title
        t2 = m.sub('', line, count=9)

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
        return t1.lower(), t2.lower()
        
    def full_paper(self, conf, title, booktitle, pages, year, key):
        # NSDI 2007 and before do not have pages
        if conf == 'iclr':
            return True
        elif conf == 'ndss':
            return True
        elif conf == 'nsdi':
            if int(year) <= 2007:
                return True
        elif conf == 'cloud':
            if int(year) == 2011 or int(year) == 2012:
                return True
        elif conf == 'sosr':
            if int(year) == 2016:
                n = int(pages)
                if n == 1 or n == 3 or n == 5 or n == 12 or n >= 15:
                    return False
                else:
                    return True
        elif conf == 'conext':
            if int(year) == 2006:
                n = int(pages)
                return True if n < 20 else False

        try:
            year = int(year)
            start, end = pages.split('-')
            if ':' in start:
                start = start.split(':')[1]
            if ':' in end:
                end = end.split(':')[1]
        except:
            return False
        if start.isdigit() and end.isdigit():
            numpages = int(end) - int(start) + 1
        else:
            return False

        if numpages < 7:
            return False
        for p in ['Poster', 'Demo', 'Experience']:
            if re.match(p, title):
                return False
        # workshop?
        if re.search('@', booktitle):
            return False
        # filter out AsiaCCS
        if conf == 'imc' or conf == 'sigcomm':
            # filter out short papers (SIGCOMM 2002-2004 and IMC)
            if numpages < 10:
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
            if numpages < 10:
                return False
        elif conf == 'sosr':
            if numpages < 9:
                return False

        elif conf == 'kdd':
            # filter out applied data science track papers
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
            # filter out operational track papers
            if year == 2014 or year == 2015 or year == 2016:
                confyear = 'nsdi{}'.format(str(year)[2:])
                if confyear in self.nsdiprogs:
                    res = self.nsdiprogs[confyear]
                else:
                    res = requests.get('https://www.usenix.org/conference/'
                        '{}/technical-sessions'.format(confyear))
                    self.nsdiprogs[confyear] = res

                ttl = ('<h2 class="node-title clearfix">'
                       '<a href="/conference/nsdi{}/technical-sessions/'
                       'presentation/'.format(str(year)[2:]))
                ttlc = re.compile(ttl)

                op = False

                if year == 2016:
                    ost = 'This paper is part of the Operational Systems Track'
                    ostc = re.compile(ost)
                    sep = ('<div id="node-[0-9]{6}" class="node node-paper '
                            'node-teaser paper-type-0 clearfix" '
                            'id="node-[0-9]{6}">')
                    sepc = re.compile(sep)

                for l in res.text.split('\n'):
                    if year == 2016:
                        if sepc.search(l):
                            op = True
                            ttl_match = False
                            continue
                        elif op:
                            if ttlc.search(l):
                                t1, t2 = CSSeniors.norm_title(title, l)
                                if t1 == t2:
                                    ttl_match = True
                            elif ostc.search(l):
                                if ttl_match:
                                    return False
                    else:
                        if re.search('technical-sessions/session/'
                                     'operational-systems-track', l):
                            op = True
                        elif re.search('technical-sessions/session/', l):
                            op = False
                        if not op:
                            continue
                        if ttlc.search(l):
                            t1, t2 = CSSeniors.norm_title(title, l)
                            if t1 == t2:
                                return False
        return True

if __name__ == '__main__':
    css = CSSeniors(sys.argv[1:], frst=False, uid=None)
    for m in css.getlog():
        if 'title' in m or 'author' in m:
            print(*list(m.values()))
        else:
            ms = {k: v for k, v in sorted(m.items(),
                key=lambda item:item[1]['latest'], reverse=True)}
            mm = ['{} ({}) ({} papers, latest {})\n'.format(k[1], k[0],
                v['#'], v['latest']) for k, v in ms.items()]
            print('co-authors: \n', *mm)
