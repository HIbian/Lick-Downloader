import os
import os.path

ui_dir = './ui'


def list_ui_file():
    return [files for files in os.listdir(ui_dir) if files.endswith('.ui')]


def rename(ui_file):
    return os.path.splitext(ui_file)[0] + '.py'


def run_main():
    cmd = 'pyuic5 -o {} {}'
    for uifile in list_ui_file():
        pyfile = os.path.join(ui_dir, rename(uifile))
        uifile = os.path.join(ui_dir, uifile)
        os.system(cmd.format(pyfile, uifile))
        print(cmd.format(pyfile, uifile))


if __name__ == "__main__":
    run_main()
