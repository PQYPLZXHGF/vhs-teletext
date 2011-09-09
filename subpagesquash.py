#!/usr/bin/env python

import sys, os
import numpy as np

from printit import do_print
from util import subcode_bcd, mrag, page
from printer import Printer

class Page(object):
    rows = np.array([0, 27, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    def __init__(self, a):
        
        self.array = a.reshape((26,42))
        #do_print("".join([chr(x) for x in self.array[0]]))
        ((self.m,self.r),e) = mrag(self.array[0][:2])
        (self.p,e) = page(self.array[0][2:4])
        (self.s,self.c),self.e = subcode_bcd(self.array[0][4:10])

        try:
            self.ds = int("%x" % self.s, 10)
        except ValueError:
            self.ds = 1000
        rows = np.array([mrag(self.array[n][:2])[0][1] for n in range(26)])
        self.goodrows = (rows == Page.rows)

    def hamming(self, other):
        h = (self.array != other.array).sum(axis=1)
        h *= self.goodrows
        return (h < 20).all() and h.sum() < 200
        #return h.sum() < 200

    def to_html(self):
        body = []

        p = Printer(self.array[0][10:])
        line = '   <span class="pgnum">P%d%02x</span> ' % (self.m,self.p) + p.string_html()
        body.append(line)

        for i in range(2,26):
            p = Printer(self.array[i][2:])
            if i == 25 and self.rows[1] == 27:
                p.set_fasttext(self.array[1], self.m)
            body.append(p.string_html())

        head = '<div class="subpage" id="%d">' % self.s

        return head + "".join(body) + '</div>'

    def to_str(self):
        return "".join([chr(x) for x in self.array.reshape((42*26))])


class Squasher(object):
    def __init__(self, filename):
        data = file(filename, 'rb')
        self.pages = []
        self.page_count = 0
        print filename,
        done = False
        while not done:
            p = data.read(42*26)
            if len(p) < (42*26):
                done = True
            else:
                a = np.fromstring(p, dtype=np.uint8)
                self.pages.append(Page(a))
                self.page_count += 1
        print "%5d" % self.page_count,

        self.subcodes = self.guess_subcodes()
        self.subcode_count = len(self.subcodes)

        unique_pages = self.hamming()
        squashed_pages = []
        for pl in unique_pages:
            squashed_pages.append(Page(self.squash(pl)))

        # sort it
        sorttmp = [(p.s, p) for p in squashed_pages]
        sorttmp.sort()
        squashed_pages = [p[1] for p in sorttmp]
        self.squashed_pages = squashed_pages

        print "%3d" % self.subcode_count, "%3d" % len(squashed_pages), "%3d" % len(unique_pages)

    def guess_subcodes(self):
        subpages = [x.ds for x in self.pages if x.ds < 0x100]
        us = set(subpages)
        sc = [(s,subpages.count(s)) for s in us]
        sc.sort()
        if sc[0][0] == 0 and sc[0][1] > (len(subpages)*0.8):
            good = [0]
        else:
            good = []
            bad = []
            for n in range(len(sc)):
                if sc[n][0] == n+1:
                    good.append(sc[n][0])
                else:
                    bad.append(sc[n][0])

        return good

    def hamming(self):
        unique_pages = []
        unique_pages.append([self.pages[0]])

        for p in self.pages[1:]:
            matched = False
            for op in unique_pages:
                if p.hamming(op[0]):
                    op.append(p)
                    matched = True
                    break
            if not matched:
                unique_pages.append([p])

        sorttmp = [(len(u),u) for u in unique_pages]
        sorttmp.sort(reverse=True)
        unique_pages = [x[1] for x in sorttmp]

        if len(unique_pages) > self.subcode_count:
            unique_pages = unique_pages[:self.subcode_count]
        self.print_this = (len(unique_pages) != self.subcode_count)

        return unique_pages

    def squash(self, pages):
        ans = np.column_stack([x.array.reshape((26*42)) for x in pages])

        auni = np.unique(ans)
        mode = np.zeros(42*26, dtype=np.uint8)
        counts = np.zeros(42*26)
        for k in auni:
            count = (ans==k).sum(-1)
            mode[count>counts] = k
            counts[count>counts] = count[count>counts] 

        final = mode.reshape((26,42))
        #if self.print_this:
        #  for i in [0]+range(2,26):
        #    do_print("".join([chr(x) for x in final[i]]))
        return final

    def to_str(self):
        return "".join([p.to_str() for p in self.squashed_pages])

    def to_html(self):
        header = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Page %d%02x</title><link rel="stylesheet" type="text/css" href="teletext.css" /></head>
<body><pre>""" % (self.squashed_pages[0].m, self.squashed_pages[0].p)
        body = "".join([p.to_html() for p in self.squashed_pages])
        footer = "</body>"

        return header+body+footer

def main_work_subdirs(gl):
    for root, dirs, files in os.walk(gl['pwd']):
        dirs.sort()
        if root == gl['pwd']:
            for d2i in dirs:
                print(d2i)

if __name__=='__main__':
    indir = sys.argv[1]
    outdir = sys.argv[2]
    of = file(outdir, 'wb')
    for root, dirs, files in os.walk(indir):
        dirs.sort()
        files.sort()
        for f in files:
            s = Squasher(os.path.join('.', root, f))
            of.write(s.to_html())
            exit(0)