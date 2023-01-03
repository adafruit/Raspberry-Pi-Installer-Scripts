#/bin/bash

# Arcade Bonnet troubleshooting tool. Checks whether prerequisite
# config and tools are present, and runs live status of inputs.

# Test if primary I2C enabled, offer help if needed
if [ ! -c /dev/i2c-1 ]
then
	echo "I2C not present. Enable with:"
	echo "  sudo raspi-config nonint do_i2c 0"
	echo "or use raspi-config 'Interface Options' menu"
	exit 1
fi

# Test if i2ctools installed, offer help if needed
if ! type i2cset >/dev/null 2>&1
then
	echo "i2c-tools not present. Install with:"
	echo "  sudo apt-get install i2c-tools"
	exit 1
fi

# MCP23017 I2C address default is 0x20, Arcade Bonnet uses 0x26:
MCP_ADDR=0x26

# registers
IODIRA=0x00
IODIRB=0x01
GPPUA=0x0C
GPPUB=0x0D
GPIOA=0x12
GPIOB=0x13

# set all pins to input
i2cset -y 1 $MCP_ADDR $IODIRA 0xFF
i2cset -y 1 $MCP_ADDR $IODIRB 0xFF

# enable internal pull up on all pins
i2cset -y 1 $MCP_ADDR $GPPUA 0xFF
i2cset -y 1 $MCP_ADDR $GPPUB 0xFF

# Display one input state, showing '*' if currently active
disp() {
	if [ $(($2 >> $3 & 0x01)) -ne 0 ]
	then
		echo " $1 :"
	else
		echo " $1 : *"
	fi
}

# Test all Arcade Bonnet inputs in a loop
while :
do
	# read pin state
	GPA=$(i2cget -y 1 $MCP_ADDR $GPIOA)
	GPB=$(i2cget -y 1 $MCP_ADDR $GPIOB)

	# report
	clear
	echo "===== BUTTONS ====="
	echo "raw value = $GPA"
	disp "1A" $GPA 0
	disp "1B" $GPA 1
	disp "1C" $GPA 2
	disp "1D" $GPA 3
	disp "1E" $GPA 4
	disp "1F" $GPA 5

	echo "==== JOYSTICKS ===="
	echo "raw value = $GPB"
	echo "4-WAY"
	disp "L" $GPB 3
	disp "R" $GPB 2
	disp "U" $GPB 1
	disp "D" $GPB 0
	echo "ANALOG"
	disp "L" $GPB 5
	disp "R" $GPB 4
	disp "U" $GPB 6
	disp "D" $GPB 7

	echo "== CTRL-C TO EXIT =="
done
