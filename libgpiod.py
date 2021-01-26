# Instructions!
# cd ~
# sudo apt-get install python3-pip
# sudo pip3 install --upgrade adafruit-python3-shell click
# wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/libgpiod.py
# sudo python3 libgpiod.py

try:
    import click
except ImportError:
    raise RuntimeError("The library 'Click' was not found. To install, try typing: sudo pip3 install Click==7.0")
try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()
shell.group = 'LIBGPIOD'

@click.command()
@click.option('-l', '--legacy', is_flag=True, help="Install a legacy version of libgpiod for systems with older libraries")
def main(legacy):
    print("""Installing build requirements - this may take a few minutes!
""")

    # install generic linux packages required
    shell.run_command("sudo apt-get update")
    shell.run_command("sudo apt-get install -y autoconf autoconf-archive automake build-essential git libtool pkg-config python3-dev python3-setuptools swig3.0 wget")

    # for raspberry pi we need...
    shell.run_command("sudo apt-get install -y raspberrypi-kernel-headers")

    build_dir = shell.run_command("mktemp -d /tmp/libgpiod.XXXX", return_output=True)
    print("""Cloning libgpiod repository to {}
""".format(build_dir))

    shell.chdir(build_dir)
    shell.run_command("git clone git://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git .")

    if legacy:
        shell.run_command("git checkout v1.4.2 -b v1.4.2")

    print("""Building libgpiod
""")

    include_path = shell.run_command("python3 -c \"from sysconfig import get_paths; print(get_paths()['include'])\"", return_output=True)

    shell.run_command("export PYTHON_VERSION=3")
    shell.run_command("./autogen.sh --enable-tools=yes --prefix=/usr/local/ --enable-bindings-python CFLAGS=\"-I/{}\" && make && sudo make install && sudo ldconfig".format(include_path))

    if shell.exists("bindings/python/.libs"):
        # This is not the right way to do this, but it works
        shell.run_command("sudo cp bindings/python/.libs/gpiod.so /usr/local/lib/python3.?/dist-packages/")
        shell.run_command("sudo cp bindings/python/.libs/gpiod.la /usr/local/lib/python3.?/dist-packages/")
        shell.run_command("sudo cp bindings/python/.libs/gpiod.a /usr/local/lib/python3.?/dist-packages/")
    shell.exit()

# Main function
if __name__ == "__main__":
    shell.require_root()
    main()
