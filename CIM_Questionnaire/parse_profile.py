#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="allyn.treshansky"
__date__ ="$Oct 1, 2013 11:28:06 AM$"

#if __name__ == "__main__":
#    print "Hello World";

import sys

from profiling import decode_profile as parse

try:
    profile = sys.argv[1]
    parse(profile)
except IndexError:
    print "Error: Please specify a profile."

