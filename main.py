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


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Front(Handler):
    def get(self):
        q_str = 'select * from Post order by created desc limit 5'
        posts = db.GqlQuery(q_str)
        self.render('front.html', posts = posts)


class PostPage(Handler):
    def get(self, *args, **kwargs):
        key = db.Key.from_path('Post', int(kwargs['id']), parent=blog_key())
        post = db.get(key)
        print key, kwargs, post

        if post:
            self.render("permalink.html", post = post)
            return

        self.error(404)


class NewPost(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


app = webapp2.WSGIApplication([ ('/', Front),
        ('/blog', Front),
        ('/blog/newpost', NewPost),
        webapp2.Route('/blog/<id:\d+>', PostPage)],
        debug=True)
