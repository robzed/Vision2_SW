# -*- coding: utf-8 -*-
# Maze related class
#
# Copyright 2016 Rob Probin.
# All original work.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from __future__ import print_function

import sys
assert sys.version_info >= (3,0)

class MazeFailedToRead(Exception):
    pass

PRINT_MAP_USES_HOME_CURSOR = False

ANSI_HOME_CURSOR = "\x1b[H"
################################################################
# 
# Maze Functions
#

class Maze(object):
    
    # value of cell data if we can't get to it
    UNREACHED = 9999     

    def __init__(self, size_of_maze, standard_target = False, init_start_wall = True):
        # need to tell engine where to head for before flood works!
        self.targets = []
        self.size = size_of_maze
        
        if standard_target:
            self.target_normal_end_cells()

        self.clear_maze_data()

        if init_start_wall:
            self.set_right_wall(0, 0, 0)

    def target_normal_end_cells(self):
        self.clear_targets()
        if self.size == 5:
            self.set_target_cell(4, 4)
        elif self.size == 16:
            self.set_target_cell(7, 7)
            self.set_target_cell(7, 8)
            self.set_target_cell(8, 7)
            self.set_target_cell(8, 8)
    
    def target_start_cell(self):
        self.clear_targets()
        self.set_target_cell(0, 0)
    
    def _apply_targets(self):
        for target in self.targets:
            row, column = target
            self.maze_cell_data[row][column] = 0

    def clear_north_south_maze_wall_data(self):
        size = self.size
        self.NS_wall_data = []
        
        # row 0
        line = []
        # for each column
        for _ in range(0, size):
            line.append(1)
        self.NS_wall_data.append(line)

        # row 1 to max
        # for each row
        for _ in range(1, size):
            line = []
            # and each column
            for _ in range(0,size):
                line.append(0)
            
            self.NS_wall_data.append(line)

        # last line, size+1
        line = []
        # column
        for _ in range(0, size):
                line.append(1)
        self.NS_wall_data.append(line)

    def clear_east_west_maze_wall_data(self):
        size = self.size
        self.EW_wall_data = []
        
        # row 1 to max
        for _ in range(0, size):
            line = []
            for column in range(0,size+1):
                if column == 0 or column == size:
                    line.append(1)
                else:
                    line.append(0)
            
            self.EW_wall_data.append(line)


    def clear_maze_cell_data(self):
        size = self.size
        self.maze_cell_data = []
        
        # for each row
        for _ in range(0, size):
            #line = []
            line = [self.UNREACHED]*size
            
            # for each column
            #for _ in range(0,size):
            #    line.append(self.UNREACHED)            # big enough for 32x32 maze would be 1024 cells!
            
            self.maze_cell_data.append(line)
        self._apply_targets()


    def clear_marks(self):
        self.marks = []
        size = self.size
        for _ in range(size):
            line = [False]*size
            self.marks.append(line)
        
    def set_mark(self, row, column):
        self.marks[row][column] = True
        
    def clear_maze_data(self):
        self.clear_north_south_maze_wall_data()
        self.clear_east_west_maze_wall_data()

        self.explored = []
        size = self.size
        for _ in range(size):
            line = [False]*size
            self.explored.append(line)

        self.clear_marks()
        
    def set_explored(self, row, column):
        self.explored[row][column] = True
    
    def print_maze(self):
        #print("Start cell is bottom left")
        if PRINT_MAP_USES_HOME_CURSOR:
            print(ANSI_HOME_CURSOR, end='')
            
        # (0,0) is bottom left
        for line in range(self.size-1, -1, -1):
            
            # line above
            line_str = []
            for column in range(0, self.size):
                if self.NS_wall_data[line+1][column]:
                    line_str.append("+----")
                else:
                    line_str.append("+    ")
            line_str.append("+")
            print("".join(line_str))

            # wall line
            line_str = []
            for column in range(0, self.size):
                if self.EW_wall_data[line][column]:
                    line_str.append("|")
                else:
                    line_str.append(" ")

                if self.marks[line][column]:
                    if self.explored[line][column]:
                        line_str.append("@%3s" % self.maze_cell_data[line][column])
                    else:
                        line_str.append("x%3s" % self.maze_cell_data[line][column])
                        
                elif self.explored[line][column]:
                    line_str.append(".%3s" % self.maze_cell_data[line][column])
                    
                else:
                    line_str.append("%4s" % self.maze_cell_data[line][column])
                
            if self.EW_wall_data[line][self.size]:
                line_str.append("|")
            else:
                line_str.append("+")
            print("".join(line_str))

        # line above
        line_str = []
        for column in range(0, self.size):
            if self.NS_wall_data[0][column]:
                line_str.append("+----")
            else:
                line_str.append("+    ")
        print("".join(line_str))

    def print_maz_format(self):
        # (0,0) is bottom left
        for line in range(self.size-1, -1, -1):
            
            # line above
            line_str = []
            for column in range(0, self.size):
                if self.NS_wall_data[line+1][column]:
                    line_str.append("+-")
                else:
                    line_str.append("+ ")
            line_str.append("+")
            print("".join(line_str))

            # wall line
            line_str = []
            for column in range(0, self.size):
                if self.EW_wall_data[line][column]:
                    line_str.append("| ")
                else:
                    line_str.append("  ")
                
            if self.EW_wall_data[line][self.size]:
                line_str.append("|")
            else:
                line_str.append("+")
            print("".join(line_str))

        # line above
        line_str = []
        for column in range(0, self.size):
            if self.NS_wall_data[0][column]:
                line_str.append("+-")
            else:
                line_str.append("+ ")
        line_str.append("+")
        print("".join(line_str))
        
    def print_stats(self):
        print("Cell data lines =", len(self.maze_cell_data))
        print("EW Wall lines =", len(self.EW_wall_data))
        print("NS wall lines =", len(self.NS_wall_data))
        print("Cell data rows =", len(self.maze_cell_data[0]))
        print("EW Wall rows =", len(self.EW_wall_data[0]))
        print("NS wall rows =", len(self.NS_wall_data[0]))
    
    def flood_adjust_one_square(self, row, column):
        cell = self.UNREACHED
        
        if not self.NS_wall_data[row+1][column]:
            cell = min(cell, self.maze_cell_data[row+1][column])
        if not self.NS_wall_data[row][column]:
            cell = min(cell, self.maze_cell_data[row-1][column])

        if not self.EW_wall_data[row][column+1]:
            cell = min(cell, self.maze_cell_data[row][column+1])
        if not self.EW_wall_data[row][column]:
            cell = min(cell, self.maze_cell_data[row][column-1])

        cell += 1   # if we have to get to it from another cell, then it will be one higher
        if cell < self.maze_cell_data[row][column]:
            self.maze_cell_data[row][column] = cell
            return True

        return False
    
    def flood_fill_all_multipass(self): #_multipass(self):
        self.clear_maze_cell_data()
        iterations = 0
        while True:
            changed = False
            for row in range(0, self.size):
                for column in range(0, self.size):
                    new_change = self.flood_adjust_one_square(row, column)
                    changed = changed or new_change
                    
            iterations += 1
            if changed == False:
                break
            
        return iterations

    def flood_fill_all(self):
        self.clear_maze_cell_data()
        cell_list = self.targets    # start from target
        while len(cell_list):
            new_list = []
            for cell in cell_list:
                row, column = cell
                new_list.extend(self._process_higher_surrounding_cells(row, column))
            cell_list = []
            for cell in new_list:
                row, column = cell
                cell_list.extend(self._process_higher_surrounding_cells(row, column))
        
#    def floor_fill_update_from_here(self, row, column):
#        pass
#
#    def start_incremental_flood_fill_from_here(self, row, column):
#        pass
#
#    def step_incremental_flood_fill_from_here(self):
#        return True

    # set_target_cell can be called multipled times (e.g. in 4 square for 16x16)
    def set_target_cell(self, row, column):
        target = (row, column)
        self.targets.append(target)

    def clear_targets(self):
        self.targets = []

    def set_front_wall(self, heading, row, column, state=True):
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return
        
        if state: state = 1
        heading &= 3
        if heading == 0:
            self.NS_wall_data[row+1][column] = state
        elif heading == 1:
            self.EW_wall_data[row][column+1] = state
        elif heading == 2:
            self.NS_wall_data[row][column] = state
        else:
            self.EW_wall_data[row][column] = state
    
    def set_left_wall(self, heading, row, column, state=True):
        self.set_front_wall(heading-1, row, column, state)

    def set_right_wall(self, heading, row, column, state=True):
        self.set_front_wall(heading+1, row, column, state=state)

    def get_front_wall(self, heading, row, column):
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return
        
        heading &= 3
        if heading == 0:
            return self.NS_wall_data[row+1][column]
        elif heading == 1:
            return self.EW_wall_data[row][column+1]
        elif heading == 2:
            return self.NS_wall_data[row][column]
        else:
            return self.EW_wall_data[row][column]
    
    def get_left_wall(self, heading, row, column):
        return self.get_front_wall(heading-1, row, column)

    def get_right_wall(self, heading, row, column):
        return self.get_front_wall(heading+1, row, column)

    def get_cell_value(self, row, column):    
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return self.UNREACHED
        return self.maze_cell_data[row][column]

    def get_next_cell_value(self, heading, row, column):
        heading &= 3

        if heading == 0:
            row += 1
        elif heading == 1:
            column += 1
        elif heading == 2:
            row -= 1
        else:
            column -= 1
        
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return self.UNREACHED

        return self.maze_cell_data[row][column]
        
    def get_lowest_directions_against_heading(self, heading, row, column):
        heading_list = []
        current = self.get_cell_value(row, column)
        
        # this order might be used to prioritse a naive implementation
        # forward first
        if not self.get_front_wall(heading, row, column):
            front = self.get_next_cell_value(heading, row, column)
            if front < current:
                heading_list.append(0)
        if not self.get_right_wall(heading, row, column):
            right = self.get_next_cell_value(heading+1, row, column)
            if right < current:
                heading_list.append(1)
        if not self.get_left_wall(heading, row, column):
            left = self.get_next_cell_value(heading-1, row, column)
            if left < current:
                heading_list.append(3)
        # back last
        if not self.get_front_wall(heading+2, row, column):
            back = self.get_next_cell_value(heading+2, row, column)
            if back < current:
                heading_list.append(2)

        return heading_list
    
    def _process_higher_surrounding_cells(self, row, column):
        # This function is called lots of times, so all the function calls have
        # been replaced with direct array accesses. This is fine because we 
        # do not need the flexibility of headings here. So the code is still
        # not confused by this.
        cell_list = []
        current = 1 + self.maze_cell_data[row][column]

        #if not self.get_front_wall(0, row, column):
        if not self.NS_wall_data[row+1][column]:
            front = self.maze_cell_data[row+1][column]
            if front > current:
                cell_list.append( (row+1, column) )
                self.maze_cell_data[row+1][column] = current
                
        #if not self.get_right_wall(0, row, column):
        if not self.EW_wall_data[row][column+1]:
            right = self.maze_cell_data[row][column+1]
            if right > current:
                cell_list.append( (row, column+1) )
                self.maze_cell_data[row][column+1] = current

        #if not self.get_left_wall(0, row, column):
        if not self.EW_wall_data[row][column]:
            left = self.maze_cell_data[row][column-1]
            if left > current:
                cell_list.append( (row, column-1) )
                self.maze_cell_data[row][column-1] = current

        # back last
        #if not self.get_front_wall(2, row, column):
        if not self.NS_wall_data[row][column]:
            back = self.maze_cell_data[row-1][column]
            if back > current:
                cell_list.append( (row-1, column) )
                self.maze_cell_data[row-1][column] = current

        return cell_list

    def parse_maz_EW(self, line, row):
        column = 0
        state = 0
        for c in line:
            if state == 1:
                if c != " ":
                    print("Failed to read space")
                    print(row)
                    raise MazeFailedToRead
            else:
                if c == "|":
                    self.set_front_wall(3, row, column, 1)
                elif c == " ":
                    self.set_front_wall(3, row, column, 0)
                else:
                    print("didn't understand")
                    print(row)
                    raise MazeFailedToRead
                
                column += 1
            state = 1 - state
    
    def parse_maz_NS(self, line, row):
        column = 0
        state = 0
        heading = 0
        if row == -1:
            heading = 2
            row = 0
        for c in line:
            if state == 0:
                if c != "+":
                    print("Failed to read +")
                    print(line)
                    raise MazeFailedToRead
            else:
                if c == "-":
                    self.set_front_wall(heading, row, column, 1)
                elif c == " ":
                    self.set_front_wall(heading, row, column, 0)
                else:
                    print("didn't understand")
                    print(line)
                    raise MazeFailedToRead
                
                column += 1
            state = 1 - state
            
    
    def parse_maz_format(self, maz_string):
        maz = maz_string.split("\n")
        expected_lines = self.size * 2 + 1
        if expected_lines != len(maz):
            print("Wrong number of lines, expected", len(maz), "actual", expected_lines)
        
        row = len(maz)-2
        for line in maz:
            if row % 2:
                self.parse_maz_NS(line, int(row/2))
            else:
                self.parse_maz_EW(line, int(row/2))
            row -= 1

    def load_example_maze(self, select=2):
        if select == 0:
            standard_maze_89iee_maz = \
"""+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   |   |   |                   |
+ + + + + +-+ + + +-+-+-+-+-+-+ +
| |   |       | |             | |
+ + +-+ +-+ + +-+ +-+-+-+-+-+ + +
|       |   |     |           | |
+ +-+ + + + +-+-+-+ +-+-+-+-+-+ +
| |   |   |                   | |
+ + + + + +-+ +-+-+-+-+-+-+-+ + +
|   |   |   |                 | |
+ + + + +-+-+ +-+-+-+-+-+-+-+-+ +
| |   |       |                 |
+ + + +-+ +-+-+ +-+-+-+-+-+-+-+ +
|   |   |     | |   |   |   |   |
+ +-+-+-+-+ + + +-+ + + + + + + +
|           | |   | | |   |   | |
+ +-+-+-+-+-+ + + + + +-+-+-+ + +
| |         | |   | |       | | |
+ + +-+-+-+ +-+-+-+ +-+-+-+ + + +
| | |       |               | | |
+ + + +-+-+-+ +-+-+-+-+ +-+-+ + +
|   | |               |       | |
+-+ + + +-+-+-+-+-+-+ +-+-+-+-+ +
|   | | |                     | |
+ + + + + +-+-+-+-+-+-+-+-+-+ + +
| | | | |             |         |
+ + + + +-+-+-+-+-+-+ + +-+-+-+ +
| | | |             | |       | |
+ + + + +-+-+-+-+-+ + +-+-+-+ + +
| | |   |           | |       | |
+ + +-+-+ + +-+-+-+-+ + +-+-+-+-+
| |       |                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
            self.parse_maz_format(standard_maze_89iee_maz)
        elif select == 1:
            UK2009final = \
"""+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |
+ + +-+-+-+-+-+-+-+-+-+-+-+-+-+ +
| | |               |         | |
+ + +-+ +-+ + +-+-+ + +-+-+-+ + +
|       |   | |     | | | | | | |
+ +-+-+ +-+-+-+ + + + + + + + + +
| | | | |       | | | | |   | | |
+ + + + +-+-+ +-+-+-+ + + +-+ + +
| | |   |             |     | | |
+ +-+ +-+-+-+-+ +-+-+ +-+-+ + + +
|             |   | |       | | |
+ +-+-+-+-+-+ +-+ + +-+ +-+-+ + +
| |         |   | |     |     | |
+ + +-+-+ + + +-+ +-+ +-+ +-+ + +
|   |     | | |   | | |     | | |
+ +-+ +-+-+ + + + + + + +-+ + + +
| |       |   |   | |   |       |
+ + +-+ +-+ + +-+-+ + +-+-+-+ + +
|   |       |       |         | |
+ +-+ +-+-+-+-+-+ + +-+-+-+-+-+ +
|                 |   | |   | | |
+ + +-+-+-+-+ + +-+ +-+ + +-+ + +
| | |       | |           |   | |
+ + + +-+ + + + +-+-+-+-+ + + + +
| |       | | |         |   | | |
+ +-+-+ + + + + +-+ + +-+ + + + +
|       | | | |     |     | | | |
+ + +-+ +-+ +-+-+-+ + +-+-+ + + +
| | |     |         |       | | |
+ + + +-+-+-+-+-+-+-+-+-+ +-+-+ +
| |                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
            self.parse_maz_format(UK2009final)
        else:
            Japan2008 = """+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |
+ +-+-+-+-+-+-+-+-+-+-+-+-+-+-+ +
| |   |   |                     |
+ + + + + + +-+-+-+-+-+-+ +-+ + +
|   |   |   | |   |   |   |   | |
+ + +-+-+-+ + + + + + + +-+ +-+ +
| |       | |   |   |   |   | | |
+ +-+-+-+ + + + + + + +-+ +-+ + +
|     |   | | |   |   |   |   | |
+-+-+ + +-+ + +-+-+-+-+ +-+ + + +
|   | |   | |   |     |     | | |
+ + + +-+ + + + + +-+ +-+-+-+ + +
| | |   | | | |   |         | | |
+ + + +-+ + +-+-+-+ +-+-+ + + + +
| |   |   | | |   |       | | | |
+ + +-+ +-+ + + + + +-+ + + + + +
| | |   | | |     | |   | | | | |
+ +-+ +-+ + + +-+-+-+ +-+ + + + +
|     |   | |           | | | | |
+-+ +-+ + + + +-+-+-+-+ + + + + +
|     | | | |             |   | |
+-+ +-+ + + +-+-+-+-+-+-+ +-+ + +
|     | | |             | |   | |
+-+ +-+ + + +-+-+-+-+ + +-+ +-+ +
|     | | | |     |   |   |   | |
+-+ +-+ + +-+ +-+ + + + + +-+ + +
|       |       |   |   |   | | |
+ +-+-+-+-+ +-+ +-+-+-+ +-+ + + +
|   |   |   |               | | |
+ + + + + + +-+-+-+-+-+ +-+ + + +
| |   |   |                 |   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"""
            self.parse_maz_format(Japan2008)


if __name__ == "__main__":
    def test():
        import timeit
        m = Maze(5, standard_target = True)
        iterations = m.flood_fill_all()
        m.set_explored(0,0)
        m.set_explored(1,0)
        m.set_mark(1,0)
        m.set_mark(2,0)
        m.print_maze()
        print(iterations)
        print()

        print()
        m = Maze(16, standard_target = True)
        m.set_front_wall(0, 1, 1)
        m.set_front_wall(1, 2, 2)
        m.set_front_wall(2, 3, 3)
        m.set_front_wall(3, 4, 4)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        print()
        m = Maze(5, standard_target = True)
        m.set_front_wall(0, 1, 1)
        m.set_left_wall(0, 1, 1)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        m.set_right_wall(0, 1, 1)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        print()
        m = Maze(5, standard_target = True)
        m.set_front_wall(1, 1, 1)
        m.set_left_wall(1, 1, 1)
        m.set_right_wall(1, 1, 1)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)
        
        m = Maze(16, standard_target = True)
        m.load_example_maze()
        time_taken = []
        for _ in range(10):
            start_time = timeit.default_timer()
            iterations = m.flood_fill_all()
            time_taken.append(timeit.default_timer() - start_time)
        print("Fast Fill Time = ", min(time_taken)*1000, "ms")
        #print("XTime = ", 100 * min(timeit.repeat(m.flood_fill_all, repeat=10, number=10)), "ms")
        m.print_maz_format()
        m.print_maze()
        print(iterations)

        n = Maze(16, standard_target = True)
        n.load_example_maze()
        time_taken = []
        for _ in range(10):
            start_time = timeit.default_timer()
            for _ in range(10):
                n.flood_fill_all_multipass()
            time_taken.append(timeit.default_timer() - start_time)
        print("Slow Fill Time = ", min(time_taken)*100, "ms")
        n.print_maze()
        
        for row in range(16):
            for column in range(16):
                if n.maze_cell_data[row][column] != m.maze_cell_data[row][column]:
                    print("Mismatch in cell data", row, column)
                    sys.exit(1)


    test()
    
    
