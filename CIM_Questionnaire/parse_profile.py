#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="allyn.treshansky"
__date__ ="$Oct 1, 2013 11:28:06 AM$"

if __name__ == "__main__":


    import hotshot.stats
    import sys

    import ipdb; ipdb.set_trace()
    stats = hotshot.stats.load(sys.argv[1])
    #stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(20)