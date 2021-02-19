#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import urllib.parse
import os.path


def usage():
    print(f'Usage: {sys.argv[0]} <m3u8 file> <dst dir> [the full m3u8 URL]')


if not(len(sys.argv) == 3 or len(sys.argv) == 4):
    usage()
    sys.exit()
m3u8file = sys.argv[1]
dstdir = sys.argv[2]
upath = False
if len(sys.argv) == 4:
    urlparse = urllib.parse.urlparse(sys.argv[3])
    (scheme, hostname, path) = (urlparse.scheme, urlparse.netloc, urlparse.path)
    path = os.path.split(path)[0]
    if len(path)==0:
        usage()
        print('  请输入正确的 URL')
        sys.exit()
    if path[-1] != '/':
        path = path + '/'
    upath = {
        "hostname": (scheme + "://" + hostname),
        "path": (scheme + "://" + hostname + path)
    }
import os
import stat


def errExit(message: str):
    print('Error: ' + message)
    sys.exit()


if not os.path.exists(m3u8file) or \
    not os.path.isfile(m3u8file) or \
        not os.access(m3u8file, os.R_OK):
    errExit(m3u8file)
if not os.path.exists(dstdir) or \
    not os.path.isdir(dstdir) or \
        not os.access(dstdir, os.W_OK):
    errExit(dstdir)
if dstdir[-1] == '/':
    dstdir = dstdir[:-1]
with open(m3u8file, 'r') as fi, \
        open(f'{dstdir}/0', 'w') as fo, \
        open(f'{dstdir}/a.m3u8', 'w') as dfo, \
        open(f'{dstdir}/a.js', 'w') as djs:
    djs.write("(function () {\n")
    djs.write("  const log = console.log;\n")
    djs.write("  const fs = require('fs');\n")
    djs.write("  const http = require('http');\n")
    djs.write("  const { URL } = require('url');\n")
    djs.write("\n")
    djs.write("  const hostname = '127.0.0.1';\n")
    djs.write("  const only_hostname = true;\n")
    djs.write("  const port = 3000;\n")
    djs.write("  let trans_files = [\n")
    i = 0
    lastfile = 'a.m3u8'
    for line in fi:
        if line == '\n':  # 空行
            continue
        if line[0] == '#':  # 注释
            dfo.write(line)
            continue
        if line[: len('http://')] == 'http://' or line[: len('https://')] == 'https://':  # 完整路径
            fo.write(line)
        elif line[0] == '/':  # 不完整绝对路径
            if not upath:
                usage()
                print('  请重新运行, 并带上 "the full m3u8 URL" 参数')
                sys.exit()
            fo.write(upath["hostname"] + line)
        else:  # 相对路径
            if not upath:
                usage()
                print('  请重新运行, 并带上 "the full m3u8 URL" 参数')
                sys.exit()
            fo.write(upath["path"] + line)
        djs.write(f"'{lastfile}',\n")
        lastfile = f'{str(i).zfill(4)}.ts'
        fo.write(f' out={lastfile}\n')
        dfo.write(f'{lastfile}\n')
        i += 1
    djs.write(f"'{lastfile}'\n")
    djs.write("  ];\n")
    djs.write("\n")
    djs.write("  (function () {\n")
    djs.write(
        "    const reg = /[0-9A-Za-z]/g, oreg = '_+-~.'; /* const reg = /[0-9A-Za-z_+-~.]/g; */\n")
    djs.write("    let files_attrs = [];\n")
    djs.write(
        "    (function init_trans_files() { trans_files.sort(); for (let i = 1; i < trans_files.length; i++) if (trans_files[i - 1] === trans_files[i]) { log(`警告: 重复指定文件: \"${trans_files[i]}\"`); trans_files.splice(i, 1); } })();\n")
    djs.write(
        "    (function conf_trans_files() { for (let i = 0; i < trans_files.length; i++) { files_attrs.push({ filename: trans_files[i], trans: false }); let t = trans_files[i], ta; ta = t; for (let c = 0; c < oreg.length; c++) while ((t = t.replace(oreg.charAt(c), '')) != ta) ta = t; const ncmpdreg = t.replace(reg, '').length !== 0; if (ncmpdreg) { log(`警告: 将不传输此文件: 文件名存在不符合正则表达式 /[0-9A-Za-z_+-~.]/ 的字符 : \"${trans_files[i]}\"`); trans_files.splice(i, 1); } } })();\n")
    djs.write("  })();\n")
    djs.write("  const filen = trans_files.length;\n")
    djs.write("\n")
    djs.write("  const server = http.createServer((req, res) => {\n")
    djs.write("    const curURL = new URL('http://hostname' + req.url);\n")
    djs.write("    const pathname = curURL.pathname;\n")
    djs.write("\n")
    djs.write("    res.removeHeader('Transfer-Encoding');\n")
    djs.write("    res.setHeader('Server', 'Apache');\n")
    djs.write("    res.setHeader('Connection', 'close');\n")
    djs.write("    let statcode = 0, haspath = false;\n")
    djs.write("    if (pathname === '/') { /* hostname */\n")
    djs.write("      statcode = 200;\n")
    djs.write(
        "      res.writeHead(200, { 'Content-Length': '0', 'Content-Type': 'text/html' });\n")
    djs.write("      res.end();\n")
    djs.write("    }\n")
    djs.write("    else {\n")
    djs.write("      for (var i = 0; i < filen; i++)\n")
    djs.write("        if (pathname === ('/' + trans_files[i])) {\n")
    djs.write("          haspath = true;\n")
    djs.write("          break;\n")
    djs.write("        }\n")
    djs.write("      if (haspath) { /* file */\n")
    djs.write("        if (fs.existsSync(trans_files[i])) { /* exists */\n")
    djs.write("          statcode = 200;\n")
    djs.write("          res.writeHead(200, {\n")
    djs.write("            'Content-Type': (pathname === '/a.m3u8' ? 'application/vnd.apple.mpegURL' : 'video/mp2t'),\n")
    djs.write("            'access-control-allow-origin': '*',\n")
    djs.write("            'access-control-allow-methods': 'POST, GET, OPTIONS'\n")
    djs.write("          });\n")
    djs.write("          fs.createReadStream(trans_files[i]).pipe(res);\n")
    djs.write("        } else { /* not exists */\n")
    djs.write("          statcode = 404;\n")
    djs.write(
        "          res.writeHead(404, { 'Content-Length': '0', 'Content-Type': 'text/html' });\n")
    djs.write("          res.end();\n")
    djs.write("        }\n")
    djs.write("      } else { /* 404 */\n")
    djs.write("        statcode = 404;\n")
    djs.write(
        "        res.writeHead(404, { 'Content-Length': '0', 'Content-Type': 'text/html' });\n")
    djs.write("        res.end();\n")
    djs.write("      }\n")
    djs.write("    }\n")
    djs.write("\n")
    djs.write("    const agent = req.headers['user-agent'];\n")
    djs.write("    log(`[${new Date().toLocaleString()}] ${req.connection.remoteAddress} - \"${req.method} ${req.url} HTTP/${req.httpVersion}\" ${statcode.toString(10)} \"${!agent ? '' : `${agent}`}\"`);\n")
    djs.write("  });\n")
    djs.write("\n")
    djs.write("  function listen_log(Message) {\n")
    djs.write("    return function () {\n")
    djs.write("      log('====================================================');\n")
    djs.write("      log('  共发布 ' + trans_files.length.toString(10) + ' 个文件');\n")
    djs.write("      log('====================================================');\n")
    djs.write("      log(Message);\n")
    djs.write("      log('file:///home/ubuntu/Downloads/m3u8player/index.html');\n")
    djs.write(
        "      log(`视频文件: http://${hostname}:${port}/a.m3u8 或者 http://localhost:${port}/a.m3u8`);\n")
    djs.write("    }\n")
    djs.write("  }\n")
    djs.write("\n")
    djs.write("  (function start_server() {\n")
    djs.write("    if (only_hostname)\n")
    djs.write(
        "      server.listen(port, hostname, listen_log(`服务运行在 http://${hostname}:${port}/`));\n")
    djs.write("    else\n")
    djs.write("      server.listen(port, listen_log(`服务在监听 ${port} 端口`));\n")
    djs.write("  })();\n")
    djs.write("})();\n")
with open(f'{dstdir}/a.py', 'w') as fo:
    fo.write("#!/usr/bin/env python3\n")
    fo.write("# -*- coding: utf-8 -*-\n")
    fo.write("import sys\n")
    fo.write("import os\n")
    fo.write("import os.path\n")
    fo.write("infile = '0'\n")
    fo.write("outfile = '00'\n")
    fo.write("\n")
    fo.write("\n")
    fo.write("def errExit(message: str):\n")
    fo.write("    print('Error: ' + message)\n")
    fo.write("    sys.exit()\n")
    fo.write("\n")
    fo.write("\n")
    fo.write("if not os.path.exists(infile) or \\\n")
    fo.write("    not os.path.isfile(infile) or \\\n")
    fo.write("        not os.access(infile, os.R_OK):\n")
    fo.write("    errExit(infile)\n")
    fo.write("with open(infile, 'r') as fi, open(outfile, 'w') as fo:\n")
    fo.write("    iterfi = fi.__iter__()\n")
    fo.write("    for line in iterfi:\n")
    fo.write("        nextline = iterfi.__next__()\n")
    fo.write("        if not os.path.exists(nextline[5:-1]):\n")
    fo.write("            fo.write(line)\n")
    fo.write("            fo.write(nextline)\n")
    fo.write("os.rename(outfile, infile)\n")
os.chmod(f'{dstdir}/a.py',
         stat.S_IRUSR |
         stat.S_IWUSR |
         stat.S_IXUSR |
         stat.S_IRGRP |
         stat.S_IROTH)
