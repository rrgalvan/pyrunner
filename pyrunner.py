"""
Defines objects objects that point to a program or script file and
methods for running it, capturing its output and post-processing it
"""
# (C) Rafa Rodríguez Galván 2017
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.

# Functions for running the script
from subprocess import Popen, PIPE
import re

# C-like structure in Python
from collections import namedtuple

class OutputLine(object):
    """
    A line from console output of any program
    """
    def __init__(self, data=""):
        self.str_data = data

    def __str__(self):
        "String identifiying current object"
        return self.str_data

    def data(self):
        return self.str_data

    def findall(self, tarjet_string):
        "Return list containing all ocurrences of string in current line"
        return re.findall(tarjet_string, self.str_data)

    def find(self, tarjet_string):
        "Return first match of string in current line"
        result = re.findall(tarjet_string, self.str_data)
        return result[0] if result else None

    def find_float(self, formated_string):
        "Return real number from first match of string in current line"
        float_re = "[-+]?([0-9]*\.[0-9]+|[0-9]+)";
        data = formated_string.format(float_re)
        return self.find(data)


class Iteration(object):
    """"
    Class defining each iteration
    It stores
       * A string defining the format which identifies begin of one interation
       * Value, type and format, for each the data stored in current iteration
    """
    def __init__(self, begin_str="iteration"):
        self.begin_format = begin_str # String identifyng begin of iteration
        self.value={} # Dictionary for store data values
        self.type={} # Dictionary for store data values
        self.format={} # Dictionary for store format used to find data

    def begin(self, line):
        "Look if current line contains begin of iteration"
        return line.find(self.begin_format)

    def data_identifiers():
        "Return list of identifiers for current data"
        return self.value.keys()

    def add_data(self, data_id, data_format, data_type=None):
        """
        Store, for each iteration, some data (for instance a real number).
          data_format: Format used to find the data in program output.
          data_id: String identifying, in each iteration, the number.
        """
        self.value[data_id] = None
        self.format[data_id] = data_format
        self.type[data_id] = data_type

    def reset_data(self):
        for data_id in self.data_identifiers():
            self.value[data_id] = None

    def find(self, data_id, line):
        data_format = self.format[data_id]
        result = None
        if(self.type[data_id]==float):
           result = line.find_float(data_format)
        if(self.type[data_id]==int):
           result = line.find_int(data_format)
        return result

class Iterator(object):
    """
    An iterator stores an iteration object and counts the number of iterations
    """
    def __init__(self, iteration):
        self.current_iteration = iteration # Current iteration
        self.count = 0 # Iteration counter

    def increase(self):
        self.count = self.count+1

class PyRunner(object):
    """
    Class for running generic programs
    """
    def __init__(self, program, path="", args={}):
        "Build a script, a program contained in a file"
        self.program = program
        self.path = path # Program path
        self.args = args # Arguments passed to the program
        self.arg_separator=' ' # Char used to separe key from value in arguments
        self.set_command(program, path, args)
        self.iterator = None

        self.save_output=True # Save output lines, by default, when running this program
        self.output_lines=[] # Array of lines from the output of the program

    def set_interpreter(self, interpreter):
        "Define the name of the intepreted which is used to run the script"
        self.interpreter = interpreter

    def get_command(self):
        "Returns the string which will be sent to the shell for running"
        return self.command

    def set_command(self, program, path, args):
        if path:
            path = self.path.rstrip("/") + "/"
        else:
            path =""
        self.command = path + self.program
        for k in self.args.keys():
            self.command = self.command + " " + k + self.arg_separator + str(self.args[k])
        return self.command

    def set_args(self,args_dict):
        """
        Introduces a set of parameters which are passed to the program.
        It is defined as a dictionary {'name': value}
        """
        self.args = args_dict
        self.set_command(self.program, self.path, self.args)

    def set_iterator(self, iterator):
        self.iterator = iterator

    def run(self, output=OutputLine):
        "Run the program (selecting from different options for running)"
        if output==None:
            return self.run_no_output()
        else:
            return self.run_get_output()

    def run_no_output(self):
        "Run the program ignoring it's console output"
        command = self.get_command()
        process = Popen(command, shell=True)
        return ()

    def run_get_output(self):
        "Run the program, yielding *realtime* output"
        command = self.get_command()
        process = Popen(command, stdout=PIPE , shell=True)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            if self.save_output:
                self.output_lines.append(line)
            yield OutputLine(line.decode('UTF-8').rstrip())


    def run_get_iterations(self):
        "Run the program, yielding *realtime* iterations"
        command = self.get_command()
        iteration = self.iterator.current_iteration
        process = Popen(command, stdout=PIPE , shell=True)

        in_some_iteration = False
        current_line = process.stdout.readline()
        # Look for begin of iteration
        print(current_line)
        while current_line and not iteration.begin(current_line):
            current_line = process.stdout.readline()
        start_new_iteration=True
        while current_line and start_new_iteration:  # Start loop on iterations
            start_new_iteration=False
            self.iterator.increase()
            iteration.reset_data()
            while current_line and not start_new_iteration: # loop on lines in current iteration
                for data_id in iteration.data_identifiers(): # For each data stored:
                    value_found = iteration.find(data_id, current_line) # Is data in current line?
                    if value_found: # Store the value found
                        print("Found, data_found=%s, data_id=%s, data_type=%s"\
                                    % (data_found, data_id, data_type) )
                        data_type = iteration.type[data_id]
                        iteration.value[data_id] = data_type(valu_found)
                    current_line = process.stdout.readline()
                    if current_line and iteration.begin(current_line):
                        start_new_iteration = True
            print("Yielding iteration")
            yield iteration


    def print_output(self):
        "Print the output of the program"
        if(self.save_output):
            for line in self.output_lines:
                print(line.decode('UTF-8').rstrip())
        else:
            print("Sorry, the output of the program was not saved")

class ScriptRunner(PyRunner):
    """
    Class for executing scripts, in the sense of short programs
    which are run by an interpreter
    """
    def __init__(self, program, path=".", args={},\
                     interpreter="", intepreter_args={}):
        PyRunner.__init__(self, program, path, args)
        self.interpreter = interpreter
        self.intepreter_args = intepreter_args
        # self.command = "{} {}".format(self.interpreter, self.get_command() )
        self.add_to_command(interpreter, intepreter_args)

    def set_interpreter_args(self, args_dict):
        """
        Introduces a set of parameters which are passed to the program.
        It is defined as a dictionary {'name': value}
        """
        self.intepreter_args = args_dict

    def add_to_command(self, interpreter, intepreter_args):
        path = self.path.rstrip("/") + "/"
        # 1. Define command as interpreter + interpreter_args
        command = interpreter
        for k in intepreter_args.keys():
            command = command + " " + k + " " + str(intepreter_args[k])
        # 2. Prepend it to script name, path and args
        self.command = command + " " + self.command
        return self.command

    def print_code(self):
        """
        Output the code lines of current script
        """
        path = self.path.rstrip("/") + "/"
        file_name = path + self.program
        # print("Printing file %s" % file_name)
        # print("---------------------------------------------------------------------------\n")
        f = open(file_name)
        for file_line in f:
            print(file_line.rstrip())


class FreeFemRunner(ScriptRunner):
    """
    Class for executing FreeFem++ scripts
    """
    def __init__(self, program, path=".", args={},\
                     interpreter="FreeFem++",
                     interpreter_args={"-ne":"", "-nw":"", "-cd":"" }):
        ScriptRunner.__init__(self, program, path, args,\
                              interpreter, interpreter_args)
