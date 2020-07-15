import glob
import pickle


if __name__ == '__main__':
    while True:
        for f in glob.glob('*.unm'):
            print(f)
        f = input('Which file: ')
        with open(f, 'rb') as f:
            print(pickle.load(f))
