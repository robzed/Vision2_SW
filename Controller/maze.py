# Maze related class
#
from __future__ import print_function


################################################################
# 
# Maze Functions
#

class Maze(object):
    def __init__(self, size_of_maze):
        # need to tell engine where to head for before flood works!
        self.targets = []
        self.size = size_of_maze
        self.clear_maze_data()

    def clear_north_south_maze_wall_data(self):
        size = self.size
        self.NS_wall_data = []
        
        # row 0
        line = []
        for column in range(0, size):
            line.append(1)
        self.NS_wall_data.append(line)

        # row 1 to max
        for row in range(1, size):
            line = []
            for column in range(0,size):
                line.append(0)
            
            self.NS_wall_data.append(line)

        # last line, size+1
        line = []
        for column in range(0, size):
                line.append(1)
        self.NS_wall_data.append(line)

    def clear_east_west_maze_wall_data(self):
        size = self.size
        self.EW_wall_data = []
        
        # row 1 to max
        for row in range(0, size):
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
        
        for row in range(0, size):
            line = []
            for column in range(0,size):
                line.append(999)            # big enough for 32x32 maze would be 1024 cells!
            
            self.maze_cell_data.append(line)

    def clear_maze_data(self):
        self.clear_north_south_maze_wall_data()
        self.clear_east_west_maze_wall_data()
        self.clear_maze_cell_data()

    def print_maze(self):
        print("Start cell is bottom left")
        
        # (0,0) is bottom left
        for line in range(self.size-1, -1, -1):
            
            # line above
            line_str = []
            for column in range(0, self.size):
                if self.NS_wall_data[line+1][column]:
                    line_str.append("+---")
                else:
                    line_str.append("+   ")
            line_str.append("+")
            print("".join(line_str))

            # wall line
            line_str = []
            for column in range(0, self.size):
                if self.EW_wall_data[line][column]:
                    line_str.append("|")
                else:
                    line_str.append(" ")
                line_str.append("%3s" % self.maze_cell_data[line][column])
                
            if self.EW_wall_data[line][self.size]:
                line_str.append("|")
            else:
                line_str.append("+")
            print("".join(line_str))

        # line above
        line_str = []
        for column in range(0, self.size):
            if self.NS_wall_data[0][column]:
                line_str.append("----")
            else:
                line_str.append("    ")
        print("".join(line_str))

    def print_stats(self):
        print("Cell data lines =", len(self.maze_cell_data))
        print("EW Wall lines =", len(self.EW_wall_data))
        print("NS wall lines =", len(self.NS_wall_data))
        print("Cell data rows =", len(self.maze_cell_data[0]))
        print("EW Wall rows =", len(self.EW_wall_data[0]))
        print("NS wall rows =", len(self.NS_wall_data[0]))

    def flood_fill_all(self):
        for target in self.targets:
            row, column = target

    def floor_fill_update_from_here(self, row, column):
        pass

    def start_incremental_flood_fill_from_here(self, row, column):
        pass

    def step_incremental_flood_fill_from_here(self):
        return True

    # set_target_cell can be called multipled times (e.g. in 4 square for 16x16)
    def set_target_cell(self, row, column):
        self.maze_cell_data[row][column] = 0
        target = (row, column)
        self.targets.append = target

    def clear_targets(self):
        self.targets = []


