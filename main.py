import argparse

from src import data_handler
from src import visualization

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Analysis of living locations based on custom criteria')
    parser.add_argument('-p', '--path_config', type=str, help='Path to config json with the list of criteria')
    args = parser.parse_args()

    map = data_handler.Map(args.path_config)
    print('Maps prepared !')

    visualization.draw_map(map)
    print('Visualization done !')