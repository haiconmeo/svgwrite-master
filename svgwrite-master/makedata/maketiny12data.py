#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: create tiny data
# Created: 30.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: GPLv3

import sys

from BeautifulSoup import BeautifulSoup
from itertools import chain

PREFACE_ATTRIBUTES = """#coding:utf-8
# generated by:  %s

from svgwrite.types import SVGAttribute

""" % __file__

PREFACE_ELEMENTS = """#coding:utf-8
# generated by:  %s

from svgwrite.types import SVGElement
from tiny12data import property_names, media_group_names

""" % __file__

class SVGProp(object):
    def __init__(self, name, anim, props):
        self.name = name
        self.anim = anim
        self.valid_types = self.get_types(props)
        self.valid_strings = self.get_strings(props)

    def __str__(self):
        return self.name

    def tostring(self):
        return "SVGAttribute('%s', anim=%s, \n    types=%s,\n    const=%s)" % (
            self.name,
            self.anim,
            self.valid_types,
            self.valid_strings)

    def get_types(self, props):
        return [ t[4:-4] for t in props if t.startswith("&lt;") ]

    def get_strings(self, props):
        return [ t[1:-1] for t in props if t.startswith("'") ]

class SVGElement(object):
    def __init__(self, name, attribute_names, property_names, possible_children):
        self.name = name
        self.attribute_names = attribute_names
        self.property_names = property_names
        self.possible_children = possible_children

    def __str__(self):
        return self.name

    def tostring(self):
        return "SVGElement('%s',\n    attributes=%s,\n    properties=%s,\n    children=%s)" % (
            self.name,
            self.attribute_names,
            self.property_names,
            self.possible_children)

def create_property_data(soup):
    table = soup.find('table', id='properties')
    tbody = table.tbody
    p = {}
    for tr in tbody.findAll('tr'):
        name = tr.find('span').contents[0][1:-1]
        td = tr.findAll('td')
        animateable = (td[1].attrs[0][1] == 'true')
        content = [t.strip() for t in td[3].getText().split('|')]
        prop = SVGProp(name, animateable, content)
        p[prop.name] = prop
    return p

def create_attribute_data(soup):
    table = soup.find('table', id='attributes')
    tbody = table.tbody
    p = {}
    for tr in tbody.findAll('tr'):
        td = tr.findAll('td')
        name = td[0].getText()
        animateable = (td[1].attrs[0][1] == 'true')
        content = [t.strip() for t in td[3].getText().split('|')]
        prop = SVGProp(name, animateable, content)
        p[prop.name] = prop
    return p

def write_properties(name, attributes, properties):
    p = {}
    p.update(attributes)
    p.update(properties)

    f = open(name, 'w')
    f.write(PREFACE_ATTRIBUTES)
    f.write("tiny12_attributes = { \n")
    keys = p.keys()
    keys.sort()
    for key in keys:
        prop = p[key]
        f.write("    '%s': %s,\n\n" % (prop.name, prop.tostring()))
    f.write("}\n\n")
    f.write("attribute_names = %s\n" % attributes.keys())
    f.write("property_names = %s\n" % properties.keys())
    f.write("media_group_names = ['audio-level', 'buffered-rendering', 'display', 'image-rendering', 'pointer-events', 'shape-rendering', 'text-rendering', 'viewport-fill', 'viewport-fill-opacity', 'visibility']\n")
    f.close()

def write_check_routines(name, routines):
    f = open(name, 'w')
    rnames = []
    for routine in routines:
        routine = routine.replace('-', '_')
        rnames.append(routine)
        f.write("def is_%s(value):\n    #return False if value if not "\
                "valid\n    return True\n\n" % routine)
    f.write("checkfuncs = {\n")
    for routine in rnames:
        f.write("    '%s': is_%s,\n" % (routine, routine))
    f.write("}")
    f.close()

def process_attributes():
    f = open("SVG12Tiny_attributeTable.html")
    soup = BeautifulSoup(f.read())
    f.close()

    attributes = create_attribute_data(soup)
    properties = create_property_data(soup)
    write_properties("tiny12attributes.py", attributes, properties)

    t = set()
    for a in chain(attributes.itervalues(), properties.itervalues()):
        t.update(a.valid_types)

    routines = list(t)
    routines.sort()

    write_check_routines("tiny12typechecker.py", routines)

def write_elements(filename, elements):
    f = open(filename, 'w')
    f.write(PREFACE_ELEMENTS)
    f.write("tiny12_elements = { \n")
    keys = elements.keys()
    keys.sort()
    for name in keys:
        element = elements[name]
        f.write("    '%s': %s,\n\n" % (name, element.tostring()))
    f.write("}\n")
    f.close()

def create_elements_data(soup):
    table = soup.find('table', id='elements')
    tbody = table.tbody
    elements = {}
    for tr in tbody.findAll('tr'):
        td = tr.findAll('td')
        name = td[0].getText()[1:-1]
        attribute_names = [a.getText() for a in td[1].findAll('a')]
        props = td[2].attrs[0][1]
        if props == 'false':
            property_names = None
        elif props == 'true':
            property_names = 'property_names'
        else:
            property_names = 'media_group_names'
        child_text = td[3].getText()
        if child_text.find('parent') != -1:
            possible_children = "['likeparent']"
        elif child_text:
            possible_children = child_text.split(',')
            try:
                possible_children.remove(u'&lt;text&gt;')
            except ValueError:
                pass
        else:
            possible_children = None
        element = SVGElement(name, attribute_names, property_names, possible_children)
        elements[element.name] = element
    return elements

def process_elements():
    f = open("SVG12Tiny_elementTable.html")
    soup = BeautifulSoup(f.read())
    f.close()
    elements = create_elements_data(soup)
    write_elements("tiny12elements.py", elements)


def main():
    process_attributes()
    process_elements()

if __name__=='__main__':
    main()
