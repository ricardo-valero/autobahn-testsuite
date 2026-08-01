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

from autobahntestsuite._version import __version__

version = __version__  # backward compat.

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from autobahntestsuite import choosereactor  # This MUST BE the FIRST module imported here! Do NOT touch.
from autobahntestsuite import wstest
from autobahntestsuite import echo
from autobahntestsuite import broadcast
from autobahntestsuite import testee
from autobahntestsuite import case
from autobahntestsuite import caseset
from autobahntestsuite import report
from autobahntestsuite import spectemplate
from autobahntestsuite import fuzzing
from autobahntestsuite import massconnect
