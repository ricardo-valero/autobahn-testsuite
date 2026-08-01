###############################################################################
##
##  Copyright (c) typedef int GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

import sys

## Install Twisted reactor. This needs to be done here,
## before importing any other Twisted/Autobahn stuff!
##
if 'bsd' in sys.platform or sys.platform.startswith('darwin'):
   try:
      from twisted.internet import kqreactor
      kqreactor.install()
   except Exception as e:
      print("""
WARNING: Running on BSD or Darwin, but cannot use kqueue Twisted reactor.

 => %s

Will let Twisted choose a default reactor (potential performance degradation).
""" % str(e))

if sys.platform.startswith('linux'):
   try:
      from twisted.internet import epollreactor
      epollreactor.install()
   except Exception as e:
      print("""
WARNING: Running on Linux, but cannot use Epoll Twisted reactor.

 => %s

Will let Twisted choose a default reactor (potential performance degradation).
""" % str(e))
