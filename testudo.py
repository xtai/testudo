#!/usr/bin/env python

import os
import json
import time

from urllib.parse import urljoin
from requests_html import HTMLSession

user_agent = 'testudo.py <https://github.com/edsu/testudo>'
www = HTMLSession()
www.headers['user-agent'] = user_agent

def get_terms(active_only=True):
    url = 'https://app.testudo.umd.edu/soc/'
    r = www.get(url)
    terms = []
    for e in r.html.find('#term-id-input option'):
        if active_only and 'selected' in e.attrs:
            terms.append(e.attrs['value'])
    return terms

def get_departments():
    url = 'https://app.testudo.umd.edu/soc/'
    r = www.get(url)
    depts = []
    for div in r.html.find('.course-prefix'):
        depts.append({
            'id': div.find('.prefix-abbrev', first=True).text,
            'name': div.find('.prefix-name', first=True).text
        })
    return depts

def get_courses(dept, term):
    url = 'https://app.testudo.umd.edu/soc/%s/%s' % (term, dept['id'])
    r = www.get(url)
    for div in r.html.find('.course'):
        yield get_course(dept, term, div)

def get_course(dept, term, div):
    course_id = div.find('.course-id', first=True).text
    return {
        'id': course_id,
        'title': div.find('.course-title', first=True).text,
        'credits': div.find('.course-min-credits', first=True).text,
        'description': t(div, '.approved-course-text') or t(div, '.course-text'),
        'grading-method': div.find('.grading-method', first=True).text.split(', '),
        'sections': get_sections(course_id, term),
        'term': term,
        'department': dept['name'],
    }

def get_sections(course_id, term):
    # 'https://app.testudo.umd.edu/soc/201801/sections?courseIds=AASP303'
    sections = []
    try:
        url = 'https://app.testudo.umd.edu/soc/%s/sections?courseIds=%s' % (term, course_id)
        r = www.get(url)
        for div in r.html.find('.section'):
            sections.append({
                'id': t(div, '.section-id'),
                'instructor': t(div, '.section-instructor'),
                'seats': t(div, '.total-seats-count'),
                'open-seats': t(div, '.open-seats-count'),
                'waitlist': t(div, '.waitlist-count'),
                'days': t(div, '.section-days'),
                'start': t(div, '.class-start-time').strip(' -'),
                'end': t(div, '.class-end-time'),
                'building': t(div, '.building-code'),
                'room': t(div, '.class-room'),
            })
    except Exception as e:
        print(e)

    time.sleep(1) # be nice
    return sections

def t(element, selector):
    e = element.find(selector, first=True)
    if e:
        return e.text
    else:
        return ''

def main():
    for term in get_terms():
        print("getting term %s" % term)
        for dept in get_departments():
            print("getting courses in %s for %s" % (term, dept['id']))
            for course in get_courses(dept, term):
                json_file = os.path.join('data', term, dept['id'], course['id'] + '.json')
                print("writing %s" % json_file)
                json_dir = os.path.dirname(json_file)
                if not os.path.isdir(json_dir):
                    os.makedirs(json_dir)
                open(json_file, 'w').write(json.dumps(course, indent=2))

if __name__ == '__main__':
    main()

