#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Monitor check md5 sum
# date: 26.06.09
# author: sikmir

import sys, string, os, traceback, re, getopt, zlib, hashlib, math
from misc import *
from subprocess import Popen

objdump, bin_dir, target = (None, None, None)
checksum = {"0": 0}
builds = []

def file_md5(file, use_system = False):
	if isinstance(file, basestring):
		if use_system:
			sysname = os.uname()[0]
		        if sysname in ('Linux', 'linux'):
            			po = Popen('md5sum -t "%s"' % file, shell=True, stdout=-1, stderr=-1)
                                po.wait()
                                m = po.stdout.readline().strip()
                                if len(m) == 32:
                                        return m
		file = open(file, 'rb')
        h = hashlib.md5()
        block = file.read(h.block_size)
        while block:
    		h.update(block)
    		block = file.read(h.block_size)
	file.close()
	return h.hexdigest()

def build_crc32_sum():
	global bin_dir, checksum, builds
        for item in builds:
    		content = ""
                flag = 0
                with open(str(bin_dir) + '/' + item + '.objdump', 'r+') as fobj:
                        for line in fobj.readlines():
                                if re.search("Contents of section", line):
                                        flag = 0
                                if re.search(".text", line) or re.search(".data", line):
                                        flag = 1
                                if flag == 1:
                                        content += line
                fobj.close()
                write_file(str(bin_dir) + '/' + item + '.objdump', content)
		checksum[item] = math.fabs(zlib.crc32(content))

def build_md5():
	global bin_dir, builds
        for item in builds:
                write_file(str(bin_dir) + '/' + str(target) + "_" + item + '.md5', \
            		file_md5(str(bin_dir) + '/' + item + '.objdump'))

def rebuild_linker():
	global checksum, builds
	for item in builds:
		content = read_file("scripts/link" + item)
		content = re.sub('__checksum = (\w+);', "__checksum = 0x%08X;" % checksum[item], content)
		write_file("scripts/link" + item, content)

def main():
	global objdump, bin_dir, target, builds
	for item in builds:
		os.system(str(objdump) + " -s " + str(bin_dir) + "/" + str(target) + "_" + \
					    item + " > " + str(bin_dir) + "/" + item + ".objdump")
	build_crc32_sum()
	build_md5()
	rebuild_linker()
	for item in builds:
		os.remove(str(bin_dir) + '/' + item + '.objdump')

if __name__=='__main__':
        try:
                opts, args = getopt.getopt(sys.argv[1:], "ho:d:t:srb", ["help", "objdump=", "bin_dir=", \
            								    "taget=", "sim", "release", "debug"])
                for o, a in opts:
                        if o in ("-h", "--help"):
                                print "Usage: checksum.py [-o <objdump>] [-d <bin_dir>] [-t <target>] [-h]\n"
                                sys.exit()
                        elif o in ("-o", "--objdump"):
                                objdump = a
                        elif o in ("-d", "--bin_dir"):
                    		bin_dir = a
                    	elif o in ("-t", "--target"):
                    		target = a
                    	elif o in ("-s", "--sim"):
                    		builds.append("sim")
                    	elif o in ("-r", "--release"):
                    		builds.append("rom")
                        elif o in ("-b", "--debug"):
                    		builds.append("ram")
                        else:
			        assert False, "unhandled option"
		main()
	except:
	        traceback.print_exc()
