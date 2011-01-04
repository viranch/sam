#!/bin/bash
mkdir -p $HOME/.sam
cp ./src/*py* $HOME/.sam/
chmod a+x $HOME/.sam/sam.pyw
chmod a+x sam
echo "Please Enter root password"
sudo cp sam /usr/bin/
echo "Successful."
