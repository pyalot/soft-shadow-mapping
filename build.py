from marshal import loads, dumps
from os import walk, stat
from os.path import exists, join, realpath, dirname, splitext, basename
from stat import ST_MTIME
from subprocess import Popen, PIPE
from datetime import datetime
from sys import argv, stdout
from tarfile import TarFile

try:
    import json
    jsonEncode = json.dumps
except ImportError:
    try:
        import cjson
        jsonEncode = cjson.encode
    except ImportError:
        try:
            import simplejson
            jsonEncode = simplejson.dumps
        except ImportError:
            sys.exit(-1)

__dir__ = dirname(realpath(__file__))

message_count = 0

class CoffeeError(Exception): pass

def message(text):
    global message_count
    now = datetime.now().strftime('%H:%M:%S')
    print '[%04i %s] %s' % (message_count, now, text)
    message_count+=1

def error(text):
    stdout.write('\x1b[31m%s\x1b[39m' % text)
    stdout.flush()

def modified(path):
    return stat(path)[ST_MTIME]

def suffix(items, suffix):
    result = []
    for item in items:
        if item.endswith(suffix):
            result.append(item)
    return result

def prefix(items, prefix):
    result = []
    for item in items:
        if item.startswith(prefix):
            result.append(item)
    return result

def files(directory):
    result = []
    for root, dirs, files in walk(directory):
        for file in files:
            result.append(join(root, file))
    return result

def preprocess(source, name):
    result = []
    for lineno, line in enumerate(source.split('\n')):
        line = line.replace('//essl', '#line %i %s' % (lineno+1, basename(name)))
        result.append(line)
    return '\n'.join(result)

def coffee_compile(name):
    message('compiling: %s' % name)
    source = open(name).read()
    source = preprocess(source, name)
    output_name = splitext(name)[0] + '.js'
    command = ['coffee', '--stdio', '--print']
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate(source)
    if process.returncode:
        error(err)
        raise CoffeeError(err)
    else:
        outfile = open(output_name, 'w')
        outfile.write(out)
        outfile.close()

def coffee_cache(filelist):
    coffees = set(suffix(filelist, '.coffee'))
    for name in coffees:
        coffee_compile(name)

if __name__ == '__main__':
    filelist = files(__dir__)
    cache = coffee_cache(filelist)
