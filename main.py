#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import jinja2
import webapp2
from google.appengine.ext import db

# set up jinja
template_dir=os.path.join(os.path.dirname(__file__), "templates")
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                             autoescape=True)


class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)


def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)


def get_posts(limit=5, offset=0):
    q_str = 'select * from Post order by created desc limit {} offset {}'.\
            format(limit, offset)
    rows = db.GqlQuery(q_str).count()
    page_rows = db.GqlQuery(q_str).count(limit=limit, offset=offset)
    result = db.GqlQuery(q_str)
    return (result, rows, page_rows)


def get_cookies(request):
    cookies = {}
    raw_cookies = request.headers.get("Cookie")
    if raw_cookies:
        for cookie in raw_cookies.split(";"):
            print cookie
            name, value = cookie.split("=")
            cookies[name] = value
    return cookies


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Front(Handler):
    def get(self):
        limit = 5
        offset = 0
        current_page = self.request.get('page')
        if current_page.isdigit():
            current_page = int(current_page)
            offset = (current_page - 1) * limit
        else:
            page = 1
        posts, rows, page_rows = get_posts(limit, offset)
        last_page = rows // limit + 1
        if rows % limit == 0:
            last_page -= 1
        self.response.set_cookie('page', str(current_page), path='/')
        self.render('front.html', posts = posts, page = current_page,
                last_page = last_page)


class NewPost(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/{}'.format(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


class Next(Handler):
    def get(self):
        cookies = get_cookies(self.request)
        current_page = cookies.get('page')
        if current_page.isdigit():
            current_page = int(current_page) + 1
        else:
            current_page = 2
        self.redirect('/blog?page={}'.format(current_page))


class PostPage(Handler):
    def get(self, *args, **kwargs):
        key = db.Key.from_path('Post', int(kwargs['id']), parent=blog_key())

        post = db.get(key)

        if post:
            self.render("permalink.html", post = post)
            return

        self.error(404)


class Prev(Handler):
    def get(self):
        cookies = get_cookies(self.request)
        current_page = cookies.get('page')
        if current_page.isdigit():
            current_page = int(current_page) - 1
        else:
            current_page = 1
        self.redirect('/blog?page={}'.format(current_page))


app = webapp2.WSGIApplication([('/', Front),
        webapp2.Route(r'/blog/<id:\d+>', PostPage),
        ('/blog', Front),
        ('/blog/', Front),
        ('/blog/prev', Prev),
        ('/blog/newpost', NewPost),
        ('/blog/next', Next)
        ],
        debug=True)
