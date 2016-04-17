# Maze related class
#
from __future__ import print_function


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
            self.clear_maze_data(just_walls = True) # avoid setting the maze cells twice
            self.target_normal_end_cells()
        else:
            self.clear_maze_data()

        if init_start_wall:
            self.set_right_wall(0, 0, 0)

    def target_normal_end_cells(self):
        self.clear_maze_cell_data()
        self.clear_targets()
        if self.size == 5:
            self.set_target_cell(4, 4)
        elif self.size == 16:
            self.set_target_cell(7, 7)
            self.set_target_cell(7, 8)
            self.set_target_cell(8, 7)
            self.set_target_cell(8, 8)
    
    def target_start_cell(self):
        self.clear_maze_cell_data()
        self.clear_targets()
        self.set_target_cell(0, 0)
    
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
            line = []
            # for each column
            for _ in range(0,size):
                line.append(self.UNREACHED)            # big enough for 32x32 maze would be 1024 cells!
            
            self.maze_cell_data.append(line)

    def clear_maze_data(self, just_walls = False):
        self.clear_north_south_maze_wall_data()
        self.clear_east_west_maze_wall_data()
        if just_walls:
            self.clear_maze_cell_data()

    def print_maze(self):
        print("Start cell is bottom left")
        
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
                line_str.append("-----")
            else:
                line_str.append("     ")
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
    
    def flood_fill_all(self):
        #for target in self.targets:
        #    row, column = target
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
        self.maze_cell_data[row][column] = 0
        target = (row, column)
        self.targets.append(target)

    def clear_targets(self):
        self.targets = []

    def set_front_wall(self, heading, row, column):
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return
        
        heading &= 3
        if heading == 0:
            self.NS_wall_data[row+1][column] = 1
        elif heading == 1:
            self.EW_wall_data[row][column+1] = 1
        elif heading == 2:
            self.NS_wall_data[row][column] = 1
        else:
            self.EW_wall_data[row][column] = 1
    
    def set_left_wall(self, heading, row, column):
        self.set_front_wall(heading-1, row, column)

    def set_right_wall(self, heading, row, column):
        self.set_front_wall(heading+1, row, column)

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
        return self.maze_cell_data[row, column]

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

        return self.maze_cell_data[row, column]
        
    def get_lowest_directions_against_heading(self, heading, row, column):
        heading_list = []
        current = self.get_cell_value(row, column)
        front = self.get_next_cell_value(heading, row, column)
        right = self.get_next_cell_value(heading+1, row, column)
        back = self.get_next_cell_value(heading+2, row, column)
        left = self.get_next_cell_value(heading-1, row, column)
        
        if front < current:
            heading_list.append(0)
        if right < current:
            heading_list.append(1)
        if back < current:
            heading_list.append(2)
        if left < current:
            heading_list.append(3)
        
        return heading_list

if __name__ == "__main__":
    def test():
        m = Maze(5)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)
        print()

        print()
        m = Maze(16)
        m.set_front_wall(0, 1, 1)
        m.set_front_wall(1, 2, 2)
        m.set_front_wall(2, 3, 3)
        m.set_front_wall(3, 4, 4)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        print()
        m = Maze(5)
        m.set_front_wall(0, 1, 1)
        m.set_left_wall(0, 1, 1)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        m.set_right_wall(0, 1, 1)
        m.flood_fill_all()
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)

        print()
        m = Maze(5)
        m.set_front_wall(1, 1, 1)
        m.set_left_wall(1, 1, 1)
        m.set_right_wall(1, 1, 1)
        iterations = m.flood_fill_all()
        m.print_maze()
        print(iterations)
        
    test()
    
    
