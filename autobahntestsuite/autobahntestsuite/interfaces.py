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

__all__ = ('IReportGenerator', )

from zope.interface import Interface, Attribute


class IReportGenerator(Interface):
   """
   A Report generator is able to produce report files (in a
   format the generator supports) from test results stored
   in a Test database.
   """

   outputDirectory = Attribute("""Default output directory base path. (e.g. 'reports/wamp/servers')""")

   fileExtension = Attribute("""Default file extension for report files (e.g. '.html').""")

   mimeType = Attribute("""Default MIME type for generated reports (e.g. 'text/html').""")


   def writeReportIndexFile(runId, file = None):
      """
      Generate a test report index and write to file like object or
      to an automatically chosen report file (under the default
      output directory

      :param runId: The test run ID for which to generate the index for.
      :type runId: object
      :param file: A file like object or None (automatic)
      :type file: object
      :returns -- None if file was provided, or the pathname
                  of the created report file (automatic).
      """

   def writeReportFile(resultId, file = None):
      """
      Generate a test report and write to file like object or
      to an automatically chosen report file (under the default
      output directory

      :param resultId: The test result ID for which to generate the report for.
      :type resultId: object
      :param file: A file like object or None (automatic)
      :type file: object
      :returns -- None if file was provided, or the pathname
                  of the created report file (automatic).
      """
